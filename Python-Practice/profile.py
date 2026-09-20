name = input("What is your name? ")
age = int(input("What is you age? "))
years = float(input("What is your years of experience? "))
isEmployed = input("Are you currently employed?  ")

print("===== Developer Profile =====")
print(f"Name            : {name}")
print(f"Age             : {age}")
print(f"Experience      : {years}")
print(f"Employed        : {isEmployed}")

print("--- Type Check ----")
print(f"name is <class '{type(name)}'")
print(f"age is <class '{type(age)}'")
print(f"experience is <class '{type(years)}'")
print(f"employed is <class '{type(isEmployed)}'")

# Ai generated
name = input("What is your name? ")
age = int(input("What is your age? "))
years = float(input("What is your years of experience? "))
employed_input = input("Are you currently employed? (yes/no) ")
is_employed = employed_input.lower() == "yes"

print("===== Developer Profile =====")
print(f"Name       : {name}")
print(f"Age        : {age}")
print(f"Experience : {years} years")
print(f"Employed   : {is_employed}")

print("\n--- Type Check ---")
print(f"name is {type(name)}")
print(f"age is {type(age)}")
print(f"experience is {type(years)}")
print(f"employed is {type(is_employed)}")