import sqlite3


def display_menu():
    # Print out numbered options
    print("Please select an option by entering a number:")
    print("1. Find accepted papers")
    print("2. Find papers assigned for review")
    print("3. Find papers with inconsistent reviews")
    print("4. Find papers according to difference score")
    print("5. Exit")
    while True:
        # While loop for prompting user again if input is invalid
        try:
            # Prompt user for an integer input
            number = int(input('Option: '))
            if 0 < number < 6:
                # Return integer if is between 1 and 5
                return number
            else:
                # Catches input if input is negative or outside of range
                print("Please select one of the options listed.")
        except(ValueError, TypeError):
            # Raise error if input is of wrong type
            print("Invalid selection. Please try again.")


def handle_email(msg):
    # Set email domain
    domain = "@Email"
    while True:
        # Prompt user for email (string)
        email = input(msg)
        if not email:
            # Catches empty strings
            print("Please enter an email.")
        elif email.endswith(domain):
            # Return email if it ends with valid domain
            return email
        else:
            # Catches invalid inputs, e.g. wrong types
            print("Invalid email. Please try again.")


def handle_values(msg, flag):
    while True:
        if flag is 3:
            # For option 3
            try:
                # Prompt user for number input
                number = float(input(msg))
                if number >= 0.0:
                    # Return input if positive and divide by 100
                    return float(number) / 100.0
                else:
                    # Catches negative numbers
                    print("Input must be positive. Please try again.")
            except (ValueError, TypeError):
                # Raise error if input is of wrong type
                print("Empty or invalid value. Please try again.")

        elif flag is 4:
            # For option 4
            try:
                # Prompt user for number input
                number = float(input(msg))
                if number >= 0.0:
                    # Return input if positive
                    return number
                else:
                    # Catches negative numbers
                    print("Input must be positive. Please try again.")
            except (ValueError, TypeError):
                # Raise error if input is of wrong type
                print("Empty or invalid value. Please try again.")


def option_1(cursor):
    # Print option 1 message
    print("\nEnter an area to list the titles of accepted papers in the given area\n"
          "in descending order of their overall review score.")
    # Prompt user for input and uppercase the string
    area = input("Area: ").upper()
    # Execute SQL statement
    cursor.execute("""
    SELECT p.title
    FROM papers p , reviews r
    WHERE decision = 'A'
    AND p.id = r.paper
    AND p.area = ?
    GROUP BY p.title
    ORDER BY AVG(r.overall) DESC;
    """, (area,))

    # Fetch all rows of query result
    rows = cursor.fetchall()
    if not rows:
        # Print message if no rows were found
        print("Given area does not exist.")
    elif rows[0][0] is None:
        # Print message if None is returned
        print("No papers were found in the given area.")
    else:
        for each in rows:
            # Print each row of query result
            print(each["title"])
    print("\n")


def option_2(cursor):
    # Print option 2 message
    print("\nEnter a user's email to list the title of papers that they were assigned to review.")
    # Prompt user for input
    email = handle_email("Email: ")
    # Execute SQL statement
    cursor.execute("""
    SELECT title
    FROM (users
    LEFT OUTER JOIN reviews
    ON users.email = reviews.reviewer) 
    LEFT OUTER JOIN papers ON reviews.paper = papers.id
    WHERE users.email = ?
    ORDER BY papers.id;
    """, (email,))

    # Fetch all rows of query result
    rows = cursor.fetchall()
    if not rows:
        # Print message if no rows were found
        print("This reviewer does not exist.")
    elif rows[0][0] is None:
        # Print message if None is returned
        print("No papers were assigned to this reviewer")
    else:
        for each in rows:
            # Print each row of query result
            print(each["title"])
    print("\n")


def option_3(cursor):
    # Print option 3 message
    print("\nEnter a percentage (X%) for which to find inconsistent papers.")
    # Set flag value for value handling function
    flag = 3
    # Set input message
    msg = "X: "
    # Get valid number input from user
    diff = handle_values(msg, flag)
    # Execute SQL statement
    cursor.execute("""
    SELECT p.id, p.title
    FROM  papers p, reviews r
    WHERE r.paper = p.id
    AND ? < ABS(1 - r.overall /
    (SELECT AVG(r2.overall)
    FROM reviews r2
    WHERE r2.paper = p.id))
    GROUP BY p.id, p.title;
    """, (diff,))

    # Fetch all rows of query result
    rows = cursor.fetchall()
    if not rows:
        # Print message if no rows were found
        print("No papers were found.")
    else:
        # Print each row of query result
        for each in rows:
            print(each["id"], each["title"])
    print("\n")


def option_4(cursor, con):
    # Print option 4 message
    print("\nEnter a range from X to Y.")
    # Set parameters for value handling function
    flag = 4
    msg_x = "X: "
    msg_y = "Y: "
    # Get valid number input from user for x and y
    x = handle_values(msg_x, flag)
    y = handle_values(msg_y, flag)
    # Execute multiple SQL statements
    cursor.executescript("""
    DROP VIEW IF EXISTS DiffScore;
    CREATE VIEW DiffScore (pid, ptitle, diff) AS
    SELECT p1.id, p1.title,
    ABS(Q3.avg_paper - Q2.avg_area)
    FROM papers p1,
    (SELECT AVG(r2.overall) AS avg_area, p2.area AS pa
    FROM reviews r2, papers p2
    WHERE r2.paper = p2.id
    GROUP BY p2.area) Q2,
    (SELECT AVG(r3.overall) AS avg_paper, r3.paper AS rp
    FROM reviews r3
    GROUP BY r3.paper) Q3 
    WHERE p1.id = Q3.rp
    AND p1.area = Q2.pa;
    """)

    # Commit change for view created
    con.commit()
    # Execute SQL statement
    cursor.execute("""
    SELECT DISTINCT u.email, u.name
    FROM DiffScore d, reviews r, users u
    WHERE d.diff >= ? AND d.diff <= ?
    AND d.pid = r.paper
    AND r.reviewer = u.email;
    """, (x, y))

    # Fetch all rows of query result
    rows = cursor.fetchall()
    if not rows:
        # Print message if no rows were found
        print("No papers were found.")
    else:
        for each in rows:
            # Print each row of query result
            print(each[0], each[1])
    print("\n")


if __name__ == "__main__":
    # Set file location
    filename = "./A3.db"
    # Establish connection to database
    conn = sqlite3.connect(filename)
    # Set row_factory to Row callable
    conn.row_factory = sqlite3.Row
    # Create cursor object
    cur = conn.cursor()
    loop = True
    # While loop which will keep going until loop = False
    while loop:
        # Displays menu
        option = display_menu()

        if option is 1:
            # Call option 1 function
            option_1(cur)

        elif option is 2:
            # Call option 2 function
            option_2(cur)

        elif option is 3:
            # Call option 3 function
            option_3(cur)

        elif option is 4:
            # Call option 4 function
            option_4(cur, conn)

        elif option is 5:
            # Print message for closing program
            print("Ending program...")
            # Set loop flag to false
            loop = False

    # Close connection to database
    conn.close()
