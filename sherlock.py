import argparse
from loguru import logger

import sherlock
from sherlock import trace, config, util
from sherlock.analysis import chrome, kernel


parser = argparse.ArgumentParser(description='Find suspicious behaviors via Perfetto')
parser.add_argument('-c', '--config_file', action='store', required=True,
                    help='file path for the config file')
parser.add_argument('-o', '--output_directory', action='store', required=True,
                    help='file path for the output directory')
parser.add_argument('-v', '--verbose',
                    action='store_true') 

def main():
    args = parser.parse_args()    
    util.set_log('DEBUG' if args.verbose else 'INFO')

    s = sherlock.AndroidDevices(config.Config(args.config_file, args.output_directory))
    s.runPerfetto()
    traces = s.collectTraces()

    tp = trace.Traces(traces)
    chrome.extractAndSaveJsFiles(tp, args.output_directory)


    s = sherlock.Sherlock(tp,
                          [kernel.detectPrivilegeEscalation, kernel.detectSuspiciousChildren, kernel.detectPrivilegeProcess])
    logger.info("Sherlock results")
    for dectector in s.results:
        logger.info(dectector)
        for result in s.results[dectector]:
            logger.info('\t' + result)

if __name__ == '__main__':
    main()