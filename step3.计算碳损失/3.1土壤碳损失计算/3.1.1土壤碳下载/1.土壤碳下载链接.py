"""
Purpose: Read the tile IDs (e.g. tileSG-001-024) from the "瓦片地址.text" file in the same directory,
and generate 25 SoilGrids OCS 0-30cm chunked download links (1-1 to 5-5) for each tile,
write all links into "下载链接.text", and record run information in "生成下载链接.log".
"""  # Top-level description: describes the script purpose and output

import os  # file and path handling
import re  # regex used to validate tile IDs
from datetime import datetime  # generate log timestamps

base_url = "https://files.isric.org/soilgrids/latest/data/ocs/ocs_0-30cm_mean/"  # base URL of the data (ends with a slash)

script_dir = os.path.dirname(os.path.abspath(__file__))  # absolute path of the current script directory
tiles_file = os.path.join(script_dir, "瓦片地址.text")  # tile address file path (same directory as the script)
output_file = os.path.join(script_dir, "下载链接.text")  # output download link file path (text suffix)
log_file = os.path.join(script_dir, "生成下载链接.log")  # log file path (append)


def log(msg: str) -> None:
    """Simple log function: print to the terminal and write to the log file"""  # function description
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # current timestamp string
    line = f"[{ts}] {msg}"  # assemble the log line
    print(line)  # print the log to the terminal
    try:
        with open(log_file, "a", encoding="utf-8") as lf:  # open the log file in append mode
            lf.write(line + "\n")  # write the log line with a newline
    except Exception:
        pass  # log write failure does not affect the main flow


def normalize_tile(value: str) -> str | None:
    """Normalize a tile string to the 'tileSG-xxx-yyy' format; return None if invalid"""  # function description
    v = value.strip()  # strip leading/trailing whitespace
    if not v:  # if empty line
        return None  # return None to ignore
    if re.fullmatch(r"tileSG-\d{3}-\d{3}", v):  # already contains the prefix and is valid
        return v  # return the original value
    if re.fullmatch(r"\d{3}-\d{3}", v):  # format with digits only
        return "tileSG-" + v  # auto-prepend the prefix and return
    return None  # other non-matching lines are treated as invalid


def generate_links() -> None:
    """Main flow: read the tile list, generate and write out all download links"""  # function description
    log("Start generating SoilGrids OCS 0-30cm download links")  # start message
    log(f"Base URL: {base_url}")  # output base URL
    log(f"Reading tile file: {tiles_file}")  # output tile file path

    if not os.path.exists(tiles_file):  # check whether the tile address file exists
        log("Tile address file does not exist; task terminated")  # notify absence
        return  # end the program directly

    valid_tiles: list[str] = []  # initialize the valid tile ID list
    invalid_lines = 0  # initialize the invalid line counter

    with open(tiles_file, "r", encoding="utf-8", errors="ignore") as f:  # open the tile address file for reading
        for line in f:  # iterate line by line
            norm = normalize_tile(line)  # normalize the current line
            if norm is None:  # if invalid or empty
                if line.strip():  # only count non-empty invalid lines
                    invalid_lines += 1  # increment the invalid line counter
                continue  # skip the current line
            valid_tiles.append(norm)  # collect the valid tile ID

    total_tiles = len(valid_tiles)  # count the total valid tiles
    log(f"Read {total_tiles} tiles; ignored {invalid_lines} invalid lines")  # output read statistics

    total_links = 0  # initialize the generated link counter

    with open(output_file, "w", encoding="utf-8") as out:  # open the output file in write mode
        for tile in valid_tiles:  # iterate over each valid tile ID
            tile_dir = tile  # the subdirectory name equals the tile ID (e.g. tileSG-001-024)
            prefix = tile  # the filename prefix equals the tile ID (e.g. tileSG-001-024)
            for i in range(1, 6):  # outer index i from 1 to 5
                for j in range(1, 6):  # inner index j from 1 to 5
                    url = f"{base_url}{tile_dir}/{prefix}_{i}-{j}.tif"  # build the full download link
                    out.write(url + "\n")  # write one link to the output file
                    total_links += 1  # increment the generated link counter

    log(f"Done: generated {total_links} links for {total_tiles} tiles")  # output completion statistics
    log(f"Download links saved to: {output_file}")  # output download link file path
    log(f"Log file location: {log_file}")  # output log file path


if __name__ == "__main__":  # standard entry point protection
    generate_links()  # call the main flow function
