import sys


DEBUG = True
program_flags = {}


def flag(flag_key, argument_type_list):
    """ A decorator to store program flags along with their appropriate function.

    Args:
        flag_key: A character coorisponding to the specific flag this program should react to.
        argument_type_list: a list of expected input types for the arguments following the flag.
    Returns:
        A reference to the original function.
    """
    def wrapper(func):
        program_flags[flag_key] = (func, argument_type_list)
        return func
    return wrapper


def debug(message, end="\n", quiet = False):
    if DEBUG:
        print(f"{'[debug] ' if not quiet else ''}{message}", end=end)


def process_flags():
    
    arguments = sys.argv

    if not len(arguments) > 1:
        debug("No flag detected\nExiting...")
        return

    flag = arguments[1]
    debug(f"Detected flag: {flag}")

    if not flag in program_flags.keys():
        debug(f"No callback registered for '{flag}'\nExiting...")
        return

    debug(f"Found a callback for flag '{flag}': {program_flags[flag]}")
    callback_arguments = program_flags[flag][1]
    debug(f"Expecting {len(callback_arguments)} argument(s)")

    if len(callback_arguments) != len(arguments) - 2:
        debug(f"Mismatched input for flag '{flag}'\n\tExpected {len(callback_arguments)} argument(s)\n\tGot {len(arguments) - 2} argument(s)")
        return
    
    debug(f"Found {len(callback_arguments)} argument(s):\n\t{'\n\t'.join(arguments[2:])}")
    debug(f"Attempting type conversion for callback. Function signature is:\n\t{program_flags[flag][1]}")

    converted_arguments = []

    for argument, expected_type in zip(arguments[2:], program_flags[flag][1]):
        try:
            debug(f"Attempting convrsion of '{argument}' to type {expected_type}", end="\n\t")
            converted_arguments.append(expected_type(argument))
        except Exception as e:
            debug(f"Conversion of '{argument}' to type {expected_type} failed:\n\t{e}")
            return
        debug("* Success *", quiet = True)

    debug("Attempting to call callback with converted arguments")

    program_flags[flag][0](*converted_arguments)


