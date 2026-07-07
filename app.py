#!/usr/bin/env python3
"""Cenithael RPG — punto de entrada."""

import argparse

from game.ui import launch


def main():
    parser = argparse.ArgumentParser(description="Cenithael RPG")
    parser.add_argument("--share", action="store_true", help="Crear enlace público Gradio")
    args = parser.parse_args()
    launch(share=args.share)


if __name__ == "__main__":
    main()
