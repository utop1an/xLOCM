from multiprocessing.pool import ThreadPool
from typing import Callable, Union


def set_timer_throw_exc(
    num_seconds: Union[float, int, None],
    exception: Callable,
    *exception_args,
    **exception_kwargs,
):
    def timer(function):
        """
        Checks that a function runs within the specified time and raises an exception if it doesn't.

        Args:
            function (function reference):
                The generator function to be wrapped with this time-checker.

        Returns:
            The wrapped function.
        """

        def wrapper(*args, **kwargs):
            # If num_seconds is None, run the function without a timeout
            if num_seconds is None:
                return function(*args, **kwargs)
            
            pool = ThreadPool(processes=1)

            thr = pool.apply_async(function, args=args, kwds=kwargs)
            # run the function for the specified seconds
            thr.wait(num_seconds)
            # return successful results, if ready
            if thr.ready():
                pool.terminate()
                return thr.get()
            else:
                # otherwise, raise an exception if the function takes too long
                raise exception(*exception_args, **exception_kwargs)

        return wrapper

    return timer


def basic_timer(num_seconds: Union[float, int]):
    def timer(function):
        """
        Runs a function for a specified time.

        Returns:
            The wrapped function.
        """

        def wrapper(*args, **kwargs):
            pool = ThreadPool(processes=1)

            thr = pool.apply_async(function, args=args, kwds=kwargs)
            # run the function for the specified seconds and exit without checking for/returning results
            thr.wait(num_seconds)
            pool.terminate()
            return

        return wrapper

    return timer

class POLOCMTimeOut(Exception):
    """
    Raised when the time it takes to complete (or attempt to complete) POLOCM is
    longer than the `max_time` attribute.
    """
    def __init__(self, max_time: float, stage: str) -> None:
        message = f"Could not complete {stage} in {max_time} seconds or less."
        super().__init__(message)

class GeneralTimeOut(Exception):
    """
    Raised when the time it takes to complete a task is longer than the generator's `max_time` attribute.
    """

    def __init__(self, max_time: float, source="Unknown"):
        message = f"Could not complete the {source} task in {max_time} seconds or less."
        super().__init__(message)


class TraceSearchTimeOut(Exception):
    """
    Raised when the time it takes to generate (or attempt to generate) a single trace is
    longer than the generator's `max_time` attribute.
    """

    def __init__(self, max_time: float):
        message = f"The generator could not find a suitable trace in {max_time} seconds or less. Change the `max_time` attribute for the trace generator used if you would like to have more time to generate a trace."
        super().__init__(message)

class TaskInitializationTimeOut(Exception):
    """
    Raised when the time it takes to initialize a task is longer than the generator's `max_time` attribute.
    """

    def __init__(self, max_time: float):
        message = f"The generator could not initialize the task in {max_time} seconds or less. Change the `max_time` attribute for the trace generator used if you would like to have more time to initialize the task."
        super().__init__(message)

class InvalidTime(Exception):
    """
    Raised when the user supplies an invalid maximum time for a trace to be generated
    to a generator.
    """

    def __init__(
        self,
        message="The provided maximum time is invalid.",
    ):
        super().__init__(message)
