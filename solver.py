import sys
import pandas as pd
import numpy as np

excluded_letter_positions = {}
known_letters = {}
eliminated_letters = []
must_contain = []

def import_word_lists():
    """Import wordlist from .txt files"""
    with open('words/wordle-allowed-guesses.txt') as f:
        guesses = f.read().splitlines()
    with open('words/wordle-answers-alphabetical.txt') as f:
        answers = f.read().splitlines()

    word_freq = pd.read_csv('words/unigram_freq.csv')
    letter_freq = pd.read_csv('words/letter_freq.csv')

    return guesses, answers, word_freq, letter_freq

def calculate_likelihood(word_list, word_freq, letter_freq):
    """Calculates the probability of a word in wordlist being the correct solution"""

    # Score word based on its frequency
    word_freq_score = word_freq[word_freq['word'].isin(word_list)]

    # Score word based on its combined letter frequency
    letter_freq_score = {}
    # for word in word_list:
    #     score = 0
    #     letters_seen = must_contain
    #     for letter in word:
    #         letter_score = letter_freq['freq'].loc[letter_freq['letter'] == letter]
    #         if letter not in letters_seen: # avoid adding the frequency score twice for repeated letters (may not want to do this)
    #             score += np.log(int(letter_score))
    #             letters_seen.append(letter) 
    #     letter_freq_score[word] = score

    return word_freq_score, letter_freq_score


def prune_list(potential_words):
    """Check for any overlap between wordlist and exclusion list"""

    # print("We know these letters are not at positions: ")
    # print(excluded_letter_positions)
    # print("We know these letters are at positions: ")
    # print(known_letters)
    # print("We know the word cannot include these letters: ")
    # print(eliminated_letters)
    # print("We know the word must contain: ")
    # print(must_contain)

    # Remove words containing eliminated letters
    pruned_list = []
    for word in potential_words:
        potentially_valid = True
        for letter in eliminated_letters:
            if letter in list(word):
                potentially_valid = False
        for index, letter in excluded_letter_positions.items():
            if word[index] == letter:
                potentially_valid = False
        if potentially_valid:
            pruned_list.append(word)


    # Retain words which have characters in correct positions and have essential letters
    possible_guesses = []
    for word in pruned_list:
        valid_word = True
        for index, letter in known_letters.items():
            if word[index] != letter:
                valid_word = False
        for letter in must_contain:
            if letter not in word:
                valid_word = False
        if valid_word:
            possible_guesses.append(word)
                
    return possible_guesses


def process_response(guess_string, response_string):
    """Updates eliminated word list"""

    guess_string = list(guess_string)
    response_string = list(response_string)

    # First, identify letters that are correct and add them to must contain list
    for i, letter in enumerate(guess_string):
        if response_string[i] != '#':
            must_contain.append(letter)

    to_remove = []
    # Update word lists depending on learned information
    for i, letter in enumerate(guess_string):
        if response_string[i] == guess_string[i]:
            # Correct letter
            known_letters[i] = letter
        elif response_string[i] == '#' and letter not in eliminated_letters:
            # Incorrect letter
            if letter in must_contain:
                # If letter is reported as incorrect, but we know it is in the word, remove the letter from other positions
                to_remove.append(letter)
            else:
                # Letter does not appear anywhere in word, so remove it
                eliminated_letters.append(letter)
                eliminated_letters.sort()

        elif response_string[i] == '/':
            # Correct letter in wrong place
            excluded_letter_positions[i] = letter

    for i, response_letter in enumerate(response_string):
        # Remove it unless the letter at the position is the removal letter
        for j, remove_letter in enumerate(to_remove):
            if response_letter != remove_letter: 
                if remove_letter in must_contain and remove_letter in known_letters:
                    # Only remove if letter at position is already known to be correct elsewhere in word
                    excluded_letter_positions[i] = remove_letter



def refine_list(guess_string, response_string, word_list, word_freq, letter_freq):
    """Refines wordlist"""

    # Update letter black and whitelists
    process_response(guess_string, response_string)

    # Remove words that cannot possibly be solutions
    new_wordlist = prune_list(word_list)

    # Calculate suitability scores based on word and letter frequency data
    word_likelihoods, letter_likelihoods = calculate_likelihood(new_wordlist, word_freq, letter_freq)

    # Take highest scoring words by each metric
    try:
        # best_letter_suggestion = sorted(letter_likelihoods.items(), key=lambda x: x[1], reverse=True)[0][0]
        best_letter_suggestion = "gary"
        best_word_suggestion = word_likelihoods.iloc[0]['word']
    except Exception as e:
        print("Error! No remaining words. Terminating...")
        sys.exit()

    return new_wordlist, best_word_suggestion, best_letter_suggestion

def main():
    """Main entry point for application"""
    # Import and concatenate word lists
    guess_list, answer_list, word_freq, letter_freq = import_word_lists()
    combined_list = guess_list + answer_list
    potential_words = combined_list

    # Display word list data
    total_words = len(combined_list)
    print(f"There are a total of {total_words} words in the database")

    # Main loop
    while len(potential_words) > 0: 
        guess_string = input("Enter a word: \n").lower()
        response_string = input("Enter response: \n").lower()

        potential_words, best_word_suggestion, best_letter_suggestion = refine_list(guess_string, response_string, potential_words, word_freq, letter_freq)

        # Display refined word list data
        remaining_words = len(potential_words)
        print(f"There are a total of {remaining_words} valid possible guesses")
        # print(f"Letter frequency recommendation: {best_letter_suggestion}")
        print(f"Engine recommendation: {best_word_suggestion}")


if __name__ == "__main__":
    main()