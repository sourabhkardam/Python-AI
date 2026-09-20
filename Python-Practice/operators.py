first = int(input("Input First Number "))
second = int(input("Input Second Number "))
print("==== Arithmetic ====")
print(f"{first} + {second} = {first+second}")
print(f"{first} - {second} = {first-second}")
print(f"{first} * {second} = {first*second}")
print(f"{first} / {second} = {first/second}")
print(f"{first} // {second} = {first//second}")
print(f"{first} % {second} = {first%second}")
print(f"{first} ** {second} = {first**second}")

age = int(input("What is your age? "))
years = float(input("What is your years of experience? "))

is_senior_dev = years >= 5
is_eligible_for_lead_role = age >= 25 and years >= 4
experienced_or_senior = years >= 5 or age >= 30
print("==== Developer Check ====")
print(f"Senior Developer : {is_senior_dev}")
print(f"Eligible for Lead: {is_eligible_for_lead_role}")
print(f"Experienced or Senior Aged: {experienced_or_senior}")

user_stack = input("What is your programming Language? ")
tech_stacks = ["Python", "Java", "Go", "Rust", "JavaScript"]
print("=== Tech Stack Check ====")
print(f"Is {user_stack} in top languages? {user_stack in tech_stacks}")

#Ai generated
first = int(input("Enter first number: "))
second = int(input("Enter second number: "))

print("===== Arithmetic =====")
print(f"{first} + {second} = {first + second}")
print(f"{first} - {second} = {first - second}")
print(f"{first} * {second} = {first * second}")
print(f"{first} / {second} = {first / second}")
print(f"{first} // {second} = {first // second}")
print(f"{first} % {second} = {first % second}")
print(f"{first} ** {second} = {first ** second}")

age = int(input("What is your age? "))
years = float(input("What are your years of experience? "))

is_senior_dev = years >= 5
is_eligible_for_lead_role = age >= 25 and years >= 4
experienced_or_senior = years >= 5 or age >= 30

print("\n===== Developer Check =====")
print(f"Senior Developer        : {is_senior_dev}")
print(f"Eligible for Lead       : {is_eligible_for_lead_role}")
print(f"Experienced or Senior   : {experienced_or_senior}")

# .strip()  → removes accidental spaces
# .title()  → capitalizes first letter: "java" → "Java"
user_stack = input("What is your programming language? ").strip().title()
tech_stacks = ["Python", "Java", "Go", "Rust", "JavaScript"]

print("\n===== Tech Stack Check =====")
print(f"Is {user_stack} in top languages? {user_stack in tech_stacks}")