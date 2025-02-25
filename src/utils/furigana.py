import argparse
import sys

from furigana_generator import FuriganaGenerator

furigana_generator: FuriganaGenerator = FuriganaGenerator()


def accept_input_continuously() -> None:
    EXIT_FLAGS: list[str] = ["q", "Q"]
    print("Input q or Q to exit.")

    while True:
        print("INPUT >", end="")
        input_text: str = input()
        if input_text in EXIT_FLAGS:
            sys.exit(0)
        else:
            output_text: str = furigana_generator.generate(text=input_text)
            print(f"OUTPUT>{output_text}\n")


def main() -> None:
    MIN_NUM_ARGS: int = 2

    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser()
    arg_parser.add_argument("-c", "--continued", action="store_true", help="enter continuous input mode")

    if len(sys.argv) < MIN_NUM_ARGS:
        arg_parser.print_usage()
        sys.exit(1)

    arg1: str = sys.argv[1]
    if arg1[0] != "-": # in case of no option
        input_text: str = arg1
        output_text: str = furigana_generator.generate(text=input_text)
        print(output_text)
    else: # in case of continuous input mode
        args: argparse.Namespace = arg_parser.parse_args()
        if args.continued:
            accept_input_continuously()


if __name__ == "__main__":
    main()