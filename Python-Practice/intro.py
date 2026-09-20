name = input("What is your name? ")
years = input("How many years of experience you have? ")
print("Hello ",name,"! You have ",years,"of experience. Welcome to Python!")

# Review Points
# Your version — works but has spacing issues
print("Hello ", name, "! You have ", years, "of experience. Welcome to Python!")
# Output: Hello  Alice ! You have  4 of experience. Welcome to Python!
#                     ^ extra space before !

# Better — using f-string
print(f"Hello {name}! You have {years} years of experience. Welcome to Python!")
# Output: Hello Alice! You have 4 years of experience. Welcome to Python!