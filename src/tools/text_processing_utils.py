import bz2
import contextlib
import json
import os
import warnings
from typing import Any, List

import cchardet  # speed up lxml (html parsing) just by importing
import joblib
import lxml
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from joblib import Parallel, delayed
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

warnings.simplefilter("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"


@contextlib.contextmanager
def tqdm_joblib(tqdm_object: tqdm):
    """
    Context manager to patch joblib to report into tqdm progress bar given as argument
    ref: https://stackoverflow.com/questions/24983493/tracking-progress-of-joblib-parallel-execution

    Parameters:
        tqdm_object (tqdm): tqdm object for multiprocessing.
    """

    class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
        def __call__(self, *args, **kwargs):
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_batch_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield tqdm_object
    finally:
        joblib.parallel.BatchCompletionCallBack = old_batch_callback
        tqdm_object.close()


def search_file_paths(dir: str, suffix: str = ".bz2") -> List[str]:
    """
    Retrieves all bz2 file paths within a specified directory.

    Parameters:
        dir (str): directory to search through.

    Returns:
        List of bz2 file path strings e.g. ['/AA/wiki_00.bz2', ..]
    """
    file_paths = []
    for subdir, _, files in os.walk(dir):
        for file in files:
            bz2_filepath = os.path.join(subdir, file)
            if bz2_filepath.endswith(suffix):
                file_paths.append(bz2_filepath[len(dir) :])
    return file_paths


def save_file_to_path(json_list: List[Any], dir: str, filepath: str) -> None:
    """
    Writes json objects to a bz2 file for a given filepath.
    """
    folderpath = dir + os.path.split(filepath)[0]
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)

    with bz2.BZ2File(dir + filepath, "wb") as bz2_f:
        for j_obj in json_list:
            json_data = json.dumps(j_obj)
            bz2_f.write(json_data.encode("utf-8"))
            bz2_f.write(b"\n")


def multiprocess_bz2(
    func: Any,
    first_loc: str,
    second_loc: str,
    third_loc: str = None,
    n_processes: int = 16,
    process_style=None,
) -> Any:
    """
    Performs multiprocessing for a given function and its filepaths.
    """
    # Get all filepaths to still process for.
    file_paths = search_file_paths(first_loc)
    exclude_paths = (
        search_file_paths(third_loc) if third_loc else search_file_paths(second_loc)
    )
    search_paths = list(set(file_paths).symmetric_difference(set(exclude_paths)))
    print(f"total files: {len(file_paths)}, pending: {len(search_paths)}")

    # Start Multiprocessing using joblib.
    with tqdm_joblib(
        tqdm(desc="Process bz2 file", total=len(search_paths))
    ) as progress_bar:
        results = Parallel(n_jobs=n_processes, prefer=process_style)(
            delayed(func)(bz2_filepath, first_loc, second_loc)
            for bz2_filepath in search_paths
        )

    return results


def remove_html_tags(sentences: List[str]) -> List[str]:
    """
    Removes html tags from string.

    Parameters:
        - sentences (List[str]): list of sentences possibly containing html tags.
    """
    result = []
    for sent in sentences:
        soup = BeautifulSoup(sent, features="lxml")
        result.append(soup.get_text(strip=False))
    return result


def get_file_iter(file: Any, filepath: str) -> tqdm:
    """
    Get progressbar for bz2 file.
    """
    file_size = sum(1 for _ in file)  # total amount of wiki articles
    file.seek(0)  # reset read pointer
    return tqdm(file, desc=f"Processing {filepath}", leave=False, total=file_size)


async def get_url(url, session):
    try:
        async with session.get(url=url) as response:
            resp = await response.read()
            return resp.decode("utf-8"), True
    except Exception as e:
        print("Unable to get url {} due to {}.".format(url, e.__class__))
        return None, False
