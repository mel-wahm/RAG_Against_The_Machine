import signal
import sys
from types import FrameType


def interrupt_hundler(singal_num: int,
                      frame: FrameType | None) -> None:
    print("\n\nOperation was stopped by the user")
    sys.exit(130)


signal.signal(signal.SIGINT, interrupt_hundler)

if __name__ == "__main__":
    import fire
    from src.rag import RAG

    # try:
    if __name__ == "__main__":
        fire.Fire(RAG("data/raw"))
    # except Exception as e:
    #     print(e)
