import hashlib

# Data values from the database (Example values)
first_name = "James"
last_name = "Walker"
gender = "1"  # Gender as string
age = "34"
weight = "76.2"
height = "177.4"
health_history = "Recently diagnosed with mild anemia"

# Print each value to check if there are any extra spaces
print(f"First Name: '{first_name}'")
print(f"Last Name: '{last_name}'")
print(f"Gender: '{gender}'")
print(f"Age: '{age}'")
print(f"Weight: '{weight}'")
print(f"Height: '{height}'")
print(f"Health History: '{health_history}'")

# Concatenate values exactly as they are in the database (no spaces)
data_string = first_name + last_name + gender + age + weight + height + health_history

# Print the concatenated string and its length to check if everything matches
print(f"Concatenated data string: '{data_string}'")
print(f"Length of concatenated string: {len(data_string)}")

# Compute the SHA-256 hash
computed_hash = hashlib.sha256(data_string.encode()).hexdigest()

# Print the computed hash
print(f"Computed Hash: {computed_hash}")

# Compare with the stored hash
stored_hash = "e4f240d780abc761cad4595002bf0ab2e191a14e343ceba25dc3695dae8444ce"  # Example stored hash
if computed_hash == stored_hash:
    print("Hashes match!")
else:
    print("Hashes do not match.")
