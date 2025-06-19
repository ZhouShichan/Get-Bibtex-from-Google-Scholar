from pathlib import Path
import argparse
from typing import Dict
from datetime import datetime

from omegaconf import OmegaConf
from loguru import logger
import tqdm

from getbibtexlib import (
    Config,
    DEFAULT_CONFIG,
    get_bibtex,
    format_bibtex,
    set_proxy,
    setup_logger,
)


def get_argparser():
    parser = argparse.ArgumentParser(description="Fetch bibtex entries based on input queries.")
    parser.add_argument(
        "--input_file",
        "-i",
        type=str,
        default="words.txt",
        help="Input file path (.txt or .bib)",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=str,
        default="outputs",
        help="Output directory to save fetched bibtex files",
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default="google_scholar",
        help="Search source (e.g., google_scholar, dblp)",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="custom",
        help="Path to global config YAML file (default: custom)",
    )
    parser.add_argument(
        "--no_query_output",
        action="store_true",
        help="Do not output query to bibtex file",
    )
    parser.add_argument("--cookie", type=str, default=None, help="Cookie for source")
    return parser


def read_input_file(path):
    """Read input lines from a txt or bib file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file {path} does not exist.")
    if not path.is_file():
        raise ValueError(f"Input path {path} is not a file.")
    if not path.suffix in [".txt", ".bib"]:
        raise ValueError(f"Input file {path} must be a .txt or .bib file, but got {path.suffix}")
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


@logger.catch
def main(args):
    setup_logger("INFO")

    # 加载配置文件
    dict_conf = OmegaConf.structured(DEFAULT_CONFIG)
    if Path(args.config).exists():
        dict_conf = OmegaConf.merge(
            dict_conf, OmegaConf.load(Path(__file__).parent / f"configs/{args.config}.yaml")
        )  # type: ignore
    dict_conf: Dict = OmegaConf.to_container(dict_conf, resolve=True)  # type: ignore
    config = Config.from_dict(dict_conf)
    if "cookie" in args and args.cookie:
        cookie_dict = {args.source: args.cookie}
        if not config.cookies:
            config.cookies = cookie_dict
        else:
            config.cookies.update(cookie_dict)

    if config.proxy.enable:
        set_proxy(config.proxy.host, str(config.proxy.port))

    # 读取输入内容
    input_file = Path(args.input_file)
    queries = read_input_file(args.input_file)

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_bib_path = output_dir / "{}-{}.bib".format(input_file.stem, datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

    # 处理每个查询
    pbar = tqdm.tqdm(total=len(queries), desc="Processing queries")
    for idx, query in enumerate(queries):
        query = query.strip()
        if not query:
            continue
        try:
            bibtex = get_bibtex(config, query, source=args.source)
            if bibtex:
                try:
                    bibtex = "{}\n\n".format(format_bibtex(bibtex))
                except Exception as e:
                    logger.error(f"Failed to format bibtex for query '{query}': {str(e)}")
                with output_bib_path.open("a") as f:
                    if not args.no_query_output:
                        f.write("% Query: {}\n".format(query.replace("\n", r"\n")))
                    f.write("% Source: {}\n".format(args.source))
                    f.write(bibtex)
            else:
                logger.warning(f"No bibtex returned for query: {query}")
        except Exception as e:
            logger.error(f"Failed processing query '{query}': {str(e)}")
        finally:
            pbar.update(1)
    pbar.close()
    logger.info("All done.")
    logger.info(f"Bibtex entries saved to {output_bib_path}")


if __name__ == "__main__":
    parser = get_argparser()
    args = parser.parse_args()
    main(args)
