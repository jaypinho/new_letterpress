import random
import string
from collections import Counter
import json
from termcolor import colored
import math

class Board:

    def __init__(self):
        self.ensure_viable_board()


    def __call__(self):
        return sum(self.cells, [])
        # return self.cells


    def __str__(self):
        return ", ".join(sum(self.cells, []))


    def ensure_viable_board(self):

        viability_verified = False

        minimum_vowels = 5
        max_same_letter = 3
        q_rule = True

        while viability_verified == False:

            self.cells = [[random.choice(string.ascii_lowercase) for _ in range(5)] for _ in range(5)]
            cells_array = sum(self.cells, [])

            # Check for minimum vowels
            if len([x for x in cells_array if x in ['a', 'e', 'i', 'o', 'u']]) < minimum_vowels:
                print('Trying again - minimum vowels', cells_array)
                continue

            # Check for max of the same letter
            if Counter(cells_array).most_common()[0][1] > max_same_letter:
                print('Trying again - maximum same letter', cells_array)
                continue

            # Check for a 'u' if there's also a 'q'
            if q_rule and 'q' in cells_array and 'u' not in cells_array:
                print('Trying again - Q without a U', cells_array)
                continue

            hard_letters = ['j', 'q', 'v', 'x', 'z']
            too_many_hard_letters = False
            for letter in hard_letters:
                if len([x for x in cells_array if x == letter]) > 2:
                    print('Trying again - too many of the same hard letter')
                    too_many_hard_letters = True
                    break
            if too_many_hard_letters:
                continue

            viability_verified = True


class Game:

    def __init__(self):
        new_board = Board()
        self.board = new_board()
        with open("wordlist-20210729.txt", "r") as vocab_file: # https://github.com/wordnik/wordlist/blob/main/wordlist-20210729.txt
        # with open("words_alpha.txt", "r") as vocab_file: # https://github.com/dwyl/english-words/blob/master/words_alpha.txt
            # vocab = vocab_file.read().splitlines()
            vocab = [x.replace('"', '') for x in vocab_file.read().splitlines()]
            self.vocabulary = vocab
        self.player1_letters = []
        self.player2_letters = []
        self.played_words = []
        self.hard_mode = True


    def __call__(self):
        
        while True:

            self.get_user_move()
            if self.check_for_winner() is not None:
                return None
            
            self.get_computer_move()
            if self.check_for_winner() is not None:
                return None


    def __str__(self):
        return json.dumps({k: v for k, v in vars(self).items() if k != 'vocabulary'})


    def check_for_winner(self):
        if len(self.player1_letters) + len(self.player2_letters) >= 25:
            if len(self.player1_letters) > len(self.player2_letters):
                print('YOU WON!')
            else:
                print('Sorry, you lost.')
            self.print_board()
            return True
        return None


    def print_board(self):

        print(self)

        square_size = int(math.sqrt(len(self.board)))
        formatted_board = ''
        for i, letter in enumerate(self.board):
            attrs = []
            if i in self.player1_letters:
                color = 'on_light_blue'
                if len(set(self.find_adjacent_letters(i)) & set(self.player1_letters)) == len(self.find_adjacent_letters(i)):
                    attrs = ['bold']
                    color = 'on_blue'
            elif i in self.player2_letters:
                color = 'on_light_red'
                if len(set(self.find_adjacent_letters(i)) & set(self.player2_letters)) == len(self.find_adjacent_letters(i)):
                    attrs = ['bold']
                    color = 'on_red'
            else:
                color = 'on_black'
            separator = '\n\n' + " ".join([str(x) if x >= 10 else f"0{str(x)}" for x in range(i, i+square_size)]) + '\n' if i % square_size == 0 else '  '
            formatted_board += separator + colored(letter.upper(), 'white', color, attrs=attrs)
        print(formatted_board)


    # Inspired by https://www.letterpressapp.com/how-to-play.html
    def is_available_word(self, word, verbose=False):

        if word in self.played_words:
            if verbose: print('Word has already been played')
            return False
        
        for played_word in self.played_words:
            if played_word.startswith(word):
                if verbose: print(f'Word is part of previously played word {played_word}')
                return False
        
        word_as_array = list(word)
        if len(word_as_array) < 2:
            if verbose: print('Word is too short')
            return False

        available_letters = list(self.board)
        for character in word_as_array:
            if character not in available_letters:
                if verbose: print('Cannot make word with letters on the board')
                return False
            available_letters.remove(character)
        
        if word not in self.vocabulary:
            if verbose: print('This is not a valid word')
            return False

        return True


    def convert_indices_to_word(self, indices):
        return "".join([self.board[x] for x in indices])


    def find_adjacent_letters(self, letter_index):

        square_size = int(math.sqrt(len(self.board)))

        row = letter_index // square_size
        col = letter_index % square_size
        adjacent_cells = []

        # Check top
        if row > 0:
            adjacent_cells.append(letter_index - square_size)
        
        # Check bottom 
        if row < square_size - 1:
            adjacent_cells.append(letter_index + square_size)

        # Check left
        if col > 0:
            adjacent_cells.append(letter_index - 1)

        # Check right
        if col < square_size - 1:  
            adjacent_cells.append(letter_index + 1)

        return adjacent_cells


    def assign_letters_to_players(self, is_player1_move, played_letters):

        # Letters fall into 5 categories:
        # 1) Neutral
        # 2) Owned by current player
        # 3) Owned and locked by current player
        # 4) Owned by opposing player
        # 5) Owned and locked by opposing player
        # On any given turn, the current player can add letters from categories 1 and/or 4

        letters_in_play = self.get_letters_in_play(is_player1_move=is_player1_move)
        for letter in played_letters:
            if letter in letters_in_play: # If it's not a locked opposing letter and it's not a letter this player already has...
                if is_player1_move:
                    self.player1_letters.append(letter)
                    if letter in self.player2_letters:
                        self.player2_letters.remove(letter)
                else:
                    self.player2_letters.append(letter)
                    if letter in self.player1_letters:
                        self.player1_letters.remove(letter)


    # Find all the letters that could be picked up by the current player in this move
    def get_letters_in_play(self, is_player1_move):

        letters_in_play = []

        for i, letter in enumerate(self.board):
            if i not in self.player1_letters and i not in self.player2_letters:
                letters_in_play.append(i)
            elif is_player1_move and i in self.player2_letters:
                adjacent_letters = self.find_adjacent_letters(i)
                if len(set(adjacent_letters) & set(self.player2_letters)) < len(adjacent_letters): # If it's not a locked opposing letter...
                    letters_in_play.append(i)
            elif is_player1_move == False and i in self.player1_letters:
                adjacent_letters = self.find_adjacent_letters(i)
                if len(set(adjacent_letters) & set(self.player1_letters)) < len(adjacent_letters): # If it's not a locked opposing letter...
                    letters_in_play.append(i)

        return letters_in_play


    def get_user_move(self):

        self.print_board()

        word_verified = False

        while word_verified == False:

            user_indices = [int(x) for x in input('\nEnter the indices of your word: ').lower().strip().split(" ")]

            if len([x for x in user_indices if x >= len(self.board)]) > 0:
                print('You used a nonexistent letter')
                continue

            user_word = self.convert_indices_to_word(user_indices)

            if self.is_available_word(user_word, verbose=True) == False:
                continue
            
            word_verified = True

        self.played_words.append(user_word)
        self.assign_letters_to_players(is_player1_move=True, played_letters=user_indices)
        print('Player 1 has played', user_word)


    def find_best_indices_for_word(self, word, board_letters):

        word_list = list(word) # The specified word as a list of characters

        indices = []
        for character in word_list:
            matching_character_found = False
            start_from_index = 0
            cur_index = None
            while matching_character_found == False:
                cur_index = next((x[0] for x in board_letters[start_from_index:] if x[1] == character), None)
                if cur_index is None: # Should only happen with words that can't be made with the letters on the board
                    return []
                if cur_index in indices:
                    start_from_index += 1
                    if start_from_index >= len(board_letters): # Should only happen with words that can't be made with the letters on the board
                        return []
                    continue
                matching_character_found = True
            indices.append(cur_index)
        return indices


    def get_computer_move(self):

        self.print_board()

        word_verified = False
        word_candidate = None

        letters_in_play = list(self.get_letters_in_play(is_player1_move=False))

        # Sort the letters on the board with the ones that are in play listed first
        board_letters = [[x[0], x[1]] for x in enumerate(self.board)]
        board_letters = sorted(board_letters, key=lambda x: x[0] in letters_in_play, reverse=True)

        while word_verified == False:

            if self.hard_mode:
                really_hard_mode = True
                if really_hard_mode: # We're in really hard mode so iterate through the entire vocabulary list in reverse order of how many letters in play that word could match against
                    vocab = sorted(self.vocabulary, key=lambda x: len(self.find_best_indices_for_word(x, board_letters)), reverse=True)
                else: # We're in hard mode so iterate through the entire vocabulary list in reverse order of word length (meaning try to play the longest words first)
                    vocab = sorted(self.vocabulary, key=len, reverse=True)
            else: # We're in easy mode so just iterate through the entire vocabulary list in order (which is usually alphabetical) 
                vocab = self.vocabulary

            for word in vocab:
                if self.is_available_word(word):
                    word_candidate = word
                    word_verified = True
                    break
        
        self.played_words.append(word_candidate)
        self.assign_letters_to_players(is_player1_move=False, played_letters=self.find_best_indices_for_word(word_candidate, board_letters))
        print('Computer has played', word_candidate)


game = Game()
game()