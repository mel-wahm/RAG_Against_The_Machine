import signal
import sys
from types import FrameType


def interrupt_handler(signal_num: int,
                      frame: FrameType | None) -> None:
    print("\n\nOperation was stopped by the user")
    sys.exit(130)


signal.signal(signal.SIGINT, interrupt_handler)

if __name__ == "__main__":
    try:
        import fire
        from src.rag import RAG
        fire.Fire(RAG("data/raw"))
    except ModuleNotFoundError as e:
        print(e)
    except Exception as e:
        print(e)
