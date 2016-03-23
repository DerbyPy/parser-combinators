Introduction to Combinatorial Parsing in Python
===============================================

Elliot Cameron | http://3noch.com

-------------------------------

What is parsing?
----------------

Let's start with a basic example of parsing.



```python
# Get the user's name and parse his first and last name.
your_name = input('Enter your full name: ')

parts_of_name = your_name.split(' ')
first_name = parts_of_name[0]
last_name = parts_of_name[-1]

print('Parsed name:', parts_of_name)
print('Hi Mr.', last_name)
```


### What did we do?

We took *raw* input and turned it into something that our program can understand and use intelligently.

Other examples:

  * The **Python interpreter** has a parser to turn my textual code into something it can execute.
  * The **Markdown** parser understands how to turn my text into something pretty.


## Grammar

Since we're transforming one thing (text) into another (meaningful data), we can describe this transformation as a set of rules, called a **grammar**.

Here's a grammar for a person's name, written in Backus-Nuar Form (BNF), a common format for grammars:

    <name>   ::= <word> " " <word>
    <word>   ::= <letter><word> | ""
    <letter> ::= "a" | "b" | "c" ...  # all the permissible symbols in a word


  * A **name** is defined by two **word**s, separated by a space.
  * A **word** is defined recursively. I'll explain.
  * A **letter** is any one of many possible symbols.
