import curses
import signal
import sys

def main(stdscr):
    # Clear the screen
    stdscr.clear()

    # Set up the dictionary of options
    options = {
        "Option 1": {"offset": 11, "size": 3233},
        "Option 2": {"offset": 22, "size": 4356},
        "Option 3": {"offset": 33, "size": 7890},
        "Option 4": {"offset": 44, "size": 1234}
    }
    selected_options = set()
    current_option = 0

    # Introductory message
    intro_message = "Select an option:"
    stdscr.addstr(0, 0, intro_message, curses.A_BOLD)

    while True:
        # Clear the screen
        stdscr.clear()

        # Display the options
        for i, (option, data) in enumerate(options.items()):
            if i == current_option:
                # Display the current option with a highlight
                stdscr.addstr(i+1, 0, "> " + option + " <", curses.A_REVERSE)
            elif i in selected_options:
                # Display a tick after the selected options
                stdscr.addstr(i+1, 0, option + " *")
            else:
                stdscr.addstr(i+1, 0, option)

        # Display the "Start" option in bold letters without the asterisk
        start_option = "Start"
        if current_option == len(options):
            stdscr.addstr(len(options)+1, 0, "> " + start_option + " <", curses.A_REVERSE)
        else:
            stdscr.addstr(len(options)+1, 0, start_option)

        # Refresh the screen
        stdscr.refresh()

        # Wait for user input
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            stdscr.refresh()
            exit()

        # Handle arrow key input
        if key == curses.KEY_UP:
            current_option = (current_option - 1) % (len(options) + 1)
        elif key == curses.KEY_DOWN:
            current_option = (current_option + 1) % (len(options) + 1)
        elif key == ord('\n'):  # Handle Enter key press
            if current_option == len(options):
                break  # Break the loop if "Start" option is selected
            else:
                # Toggle the selection of the current option
                if current_option in selected_options:
                    selected_options.remove(current_option)
                else:
                    selected_options.add(current_option)

    if len(selected_options) > 0:
        # Print the selected options after the loop
        print("Selected options:")
        for option_idx in selected_options:
            option_name = list(options.keys())[option_idx]
            print(option_name)

    # Clean up the curses environment
    curses.endwin()


# Set up the curses environment
curses.wrapper(main)
