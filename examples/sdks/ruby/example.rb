# Example: Using the PeaLang Ruby SDK
#
# Generate the SDK:
#   pea sdk generate ruby ./sdk
#
# Run:
#   ruby example.rb

require_relative './sdk/lib/pealang/client'

client = PeaLang::SdkClient.new('http://localhost:8080')

# Health check
health = client.health
puts "Health: #{health}"

# Invoke add function from math_utils module
result1 = client.invoke('math_utils', 'add', ['3', '7'])
puts "3 + 7 = #{result1}"

# Invoke multiply function
result2 = client.invoke('math_utils', 'multiply', ['4', '5'])
puts "4 * 5 = #{result2}"

# Invoke greet function
result3 = client.invoke('math_utils', 'greet', ['World'])
puts result3
