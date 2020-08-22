# -*- coding: utf-8 -*-
from math import ceil

from .graver import GRAMMAR_CHARS, GravedDescription, GravedCodeBlock, GravedTable, GravedListing, \
    GRAVE_TYPE_GLOBAL_REFERENCE

INDENT_SIZE_DEFAULT = 4

SPACE_CHAR_DEFAULT = ' '
SPACE_CHAR_UNICODE = (b'\xe2\xa0\x80').decode()

DEFAULT_LISTING_HEAD = '-'*(INDENT_SIZE_DEFAULT<<4)

EMBED_DESCRIPTION_MAX_SIZE = 2048

def sizify(words, max_length):
    """
    Builds chunks from the given words, which do not extend the given size.
    
    Parameters
    ----------
    words : `list` of `str`
        The words to build the lines from.
    max_length : `int`
        The maximal length of a generated line.
    
    Returns
    -------
    lines : `list` of `str`
    """
    lines = []
    if words is None:
        return lines
    
    actual_line = []
    line_length = 0
    for word in words:
        word_length = len(word)
        line_length += 1+word_length
        if line_length <= max_length:
            actual_line.append(word)
            continue
        
        if len(actual_line) == 1:
            line = actual_line.pop(0)
            line_length = 0
        else:
            line = ' '.join(actual_line)
            actual_line.clear()
            line_length = word_length
        
        actual_line.append(word)
        lines.append(line)
        continue
    
    if len(actual_line) == 1:
        line = actual_line[0]
    else:
        line = ' '.join(actual_line)
    
    lines.append(line)
    
    return lines

def graved_to_words(graved):
    """
    Translates the given graved content to words.
    
    Parameters
    ----------
    graved : `None` or `list` of (`str`, ``Grave``) elements
    
    Returns
    -------
    words : `None` or `list` of `str`
    """
    if graved is None:
        return None
    
    words = []
    for element in graved:
        if type(element) is str:
            if words:
                last = words[-1]
                starter = last[0]
                if element[0] in GRAMMAR_CHARS:
                    add_space_before = False
                elif starter == '`':
                    add_space_before = True
                else:
                    add_space_before = True
            else:
                add_space_before = False
            
            local_words = element.split(' ')
            if (not add_space_before) and words:
                words[-1] = words[-1]+local_words.pop(0)
            
            words.extend(local_words)
        
        else:
            local_word = f'`{element.content}`'
            words.append(local_word)
    
    return words

def graved_to_source_words(graved):
    """
    Translates the given graved content back to source like words.
    
    Parameters
    ----------
    graved : `None` or `list` of (`str`, ``Grave``) elements
    
    Returns
    -------
    words : `None` or `list` of `str`
    """
    if graved is None:
        return None
    
    words = []
    for element in graved:
        if type(element) is str:
            if words:
                last = words[-1]
                starter = last[0]
                if element[0] in GRAMMAR_CHARS:
                    add_space_before = False
                elif starter == '`':
                    add_space_before = True
                else:
                    add_space_before = True
            else:
                add_space_before = False
            
            local_words = element.split(' ')
            if (not add_space_before) and words:
                words[-1] = words[-1]+local_words.pop(0)
            
            words.extend(local_words)
            
        else:
            if element.type == GRAVE_TYPE_GLOBAL_REFERENCE:
                graver = '``'
            else:
                graver = '`'
            
            local_word = f'{graver}{element.content}{graver}'
            words.append(local_word)
    
    return words

class BuilderContext(object):
    """
    Builder context for converters.
    
    Parameters
    ----------
    indent : `int`
        A pregenerated indention.
    indent_size : `int`
        The size of an indent.
    max_line_length : `int`
        The maximal length of a generated line.
    space_char : `str`
        The character what is used when building tables and indents.
    word_converter : `fucntion`
        Converter to transform graved content to words.
    """
    __slots__ = ('indent', 'indent_size', 'max_line_length', 'space_char', 'word_converter')
    def __init__(self, indent_size, space_char, max_line_length, word_converter):
        self.indent_size = indent_size
        self.space_char = space_char
        self.word_converter = word_converter
        self.max_line_length = max_line_length
        self.indent = indent_size*space_char
    
    def __repr__(self):
        """Returns the builder context's represnetation."""
        return (f'{self.__class__.__name__}(indent_size={self.indent_size!r}, max_line_length='
            f'{self.max_line_length!r}, space_char={self.space_char!r}, word_converter={self.word_converter!r})')

EMBED_SIZED_BUILDER_CONTEXT = BuilderContext(INDENT_SIZE_DEFAULT, SPACE_CHAR_UNICODE, 80, graved_to_words)
TEXT_BUILDER_CONTEXT = BuilderContext(INDENT_SIZE_DEFAULT, SPACE_CHAR_DEFAULT, 120, graved_to_words)
TEXT_SOURCE_BUILDER_CONTEXT = BuilderContext(INDENT_SIZE_DEFAULT, SPACE_CHAR_DEFAULT, 120, graved_to_source_words)

class TableLine(object):
    """
    Represnets a line inside of a table.
    
    Attributes
    ----------
    lines : `list` of `str`
        The lines, to what the respective table row is broken down.
    """
    def __init__(self, indent_level, line, sizes, builder_context):
        """
        Creates a new tabel line instance.
        
        Parameters
        ----------
        indent_level : `int`
            How much the respective table is indented.
        line : `list` of (`None`, `str`, `list` of `str`)
            The generated line(s) of the represneted line of the table.
        sizes : `list` of `int`
            The internal size for each column.
        builder_context : ``BuilderContext``
            Context to define some building details.
        """
        longest = 1
        for line_part in line:
            if type(line_part) is str:
                continue
            
            length = len(line_part)
            if length > longest:
                longest = length
        
        lines = []
        
        for index in range(longest):
            # Add indent
            result_line = []
            for _ in range(indent_level):
                result_line.append(builder_context.indent)
            
            # Add starter
            result_line.append('|')
            
            for column_index in range(len(line)):
                result_line.append(builder_context.space_char)
                part = line[column_index]
                if part is None:
                    result_line.append(builder_context.space_char*sizes[column_index])
                
                if type(part) is str:
                    if index:
                        result_line.append(builder_context.space_char*sizes[column_index])
                    else:
                        result_line.append(part)
                        result_line.append(builder_context.space_char*(sizes[column_index]-len(part)))
                        continue
                
                if len(part) <= index:
                    result_line.append(builder_context.space_char*sizes[column_index])
                else:
                    part = part[index]
                    result_line.append(part)
                    result_line.append(builder_context.space_char*(sizes[column_index]-len(part)))
                
                result_line.append(builder_context.space_char)
                result_line.append('|')
            
            result_line.append('\n')
            generated_line = ''.join(result_line)
            lines.append(generated_line)
        
        self.lines = lines
    
    @property
    def line_count(self):
        """
        Returns to how much lines the given row is
        
        Returns
        -------
        length : `int`
        """
        return len(self.lines)
    
    @property
    def character_count(self):
        """
        Returns how much character teh given row is from.
        
        Returns
        -------
        length : `int`
        """
        length = 0
        for line in self.lines:
            length+=len(line)
        
        return length

class TableConverter(object):
    """
    Converter class for tables, when building text.
    
    Attributes
    ----------
    head_under_line : `str`
        Seperataor line after the first line of the table.
    lines : `list` of `str`
        The lines of the table.
    separator_line : `str`
        Separator line between all lines of the table (expect the first two).
    """
    __slots__ = ('head_under_line', 'lines', 'separator_line')
    def __new__(cls, table, indent_level, optimal_fit, builder_context):
        """
        Creates a new table to text converter.
        
        Parameters
        ----------
        table : ``GravedTable``
            The source table.
        indent_level : `int`
            The number of how far is the table indented.
        optimal_fit : `int`
            The preferred maximal line length of the table.
        builder_context : ``BuilderContext``
            Context to define some building details.
        
        Yields
        ------
        self : ``TableConverter``
        """
        x, y = table.size
        lines = []
        for line in table:
            new_line = [builder_context.word_converter(part) for part in line]
            lines.append(new_line)
        
        # calculate part lengths for each column
        longest_lengths = [0 for _ in range(x)]
        
        for line in lines:
            for index in range(x):
                part = line[index]
                if part is None:
                    continue
                
                length = len(part) -1
                for word in part:
                    length +=len(word)
                
                if longest_lengths[index] < length:
                    longest_lengths[index] = length
        
        fillable_chars = optimal_fit - (x+1) - ((x-1)<<1)
        # do we fit?
        if sum(longest_lengths) <= fillable_chars:
            sizes = longest_lengths
        else:
            # calculate minimal lengths, aka longest word's length for each column
            shortest_lengths = [0 for _ in range(x)]
            for line in lines:
                for index in range(x):
                    part = line[index]
                    if part is None:
                        continue
                    
                    length = 0
                    
                    for word in part:
                        word_length = len(word)
                        if length < word_length:
                            length = word_length
                    
                    if shortest_lengths[index] < length:
                        shortest_lengths[index] = length
            
            # calculate average lengths
            average_lengths = [0 for _ in range(x)]
            for line in lines:
                for index in range(x):
                    part = line[index]
                    if part is None:
                        continue
                    
                    length = len(line) -1
                    for word in part:
                        length +=len(word)
                    
                    longest_lengths[index] += length
            
            for index in range(x):
                length =  average_lengths[index] / y
                length = ceil(length)
                average_lengths[index] = length
            
            size_factors = [
                (((average_lengths[index]<< 1) + longest_lengths[index])*shortest_lengths[index])**.5 \
                    for index in range(x)]
            
            factorizbale_chars = fillable_chars - sum(shortest_lengths)
            
            if factorizbale_chars <= 40:
                if x == 1:
                    median_shortest = shortest_lengths[0]
                else:
                    sorted_shortest = sorted(shortest_lengths)
                    if x&1:
                        median_shortest = sorted_shortest[x>>1]
                    else:
                        median_shortest = ceil((sorted_shortest[x>>1] + sorted_shortest[(x+1)>>1] / 2.0))
                
                factor =  ((-factorizbale_chars) + median_shortest)
            else:
                factor =  factorizbale_chars
            
            factor = factor / fillable_chars
            
            sizes = [ceil(size_factors[index]*factor + shortest_lengths[index]) for index in range(x)]
            
            for line in lines:
                for index in range(x):
                    line[index] = sizify(line[index], sizes[index])
            
            sizes = [0 for _ in range(x)]
            
            for line in lines:
                for index in range(x):
                    line_parts = line[index]
                    for part in line_parts:
                        length = len(part)
                        
                        if sizes[index] < length:
                            sizes[index] = length
        
        generated_lines = [TableLine(indent_level, line, sizes, builder_context) for line in lines]
        
        result_line = []
        for _ in range(indent_level):
            result_line.append(builder_context.indent)
        
        for length in sizes:
            result_line.append('+')
            result_line.append('='*(length+2))
        
        result_line.append('+\n')
        
        head_under_line = ''.join(result_line)
        result_line.clear()
        for _ in range(indent_level):
            result_line.append(builder_context.indent)
        
        for length in sizes:
            result_line.append('+')
            result_line.append('-'*(length+2))
        
        result_line.append('+\n')
        
        separator_line = ''.join(result_line)
        
        self = object.__new__(cls)
        self.head_under_line = head_under_line
        self.lines = generated_lines
        self.separator_line = separator_line
        yield self
    
    @property
    def character_count(self):
        """
        Returns the table's characters' total length.
        
        Returns
        -------
        length : `int`
        """
        lines = self.lines
        length = (len(lines)+1)*len(self.separator_line)
        for line in lines:
            length += line.character_count
        
        return length
    
    @property
    def row_count(self):
        """
        Returns the table's row count.
        
        Returns
        -------
        length : `int`
        """
        return len(self.lines)
    
    @property
    def line_count(self):
        """
        Returns the table's total line count.
        
        Returns
        -------
        length : `int`
        """
        lines = self.lines
        length = len(lines)+1
        for line in lines:
            length += line.line_count
        
        return length
    
    def _do_break(self, number_of_rows):
        """
        Does break after the given amount of rows.
        
        Parameters
        ----------
        number_of_rows : `int`
            The number of rows after the table should be broken.
        
        Returns
        -------
        table_1 : ``TableConverter``
        table_2 : ``TableConverter``
        """
        number_of_rows +=1
        lines = self.lines
        head = lines[0]
        
        table_1 = object.__new__(type(self))
        table_1.head_under_line = self.head_under_line
        table_1.lines = [head, *lines[1:number_of_rows]]
        table_1.separator_line = self.separator_line
        
        table_2 = object.__new__(type(self))
        table_2.head_under_line = self.head_under_line
        table_2.lines = [head, *lines[number_of_rows:]]
        table_2.separator_line = self.separator_line
        
        return table_1, table_2
    
    def _test_break(self):
        """
        Returns whether this table should be rendered alone as a broken part of a bigger table.
        
        Returns
        -------
        passed : `bool`
        """
        if self.row_count < 2:
            return False
        
        if self.line_count < 7:
            return False
        
        return True
    
    def do_break(self, number_of_chars):
        """
        Breaks the table to parts an returns the most optimal case for the given max chars.
        
        Parameters
        ----------
        number_of_chars : `int`
            The maximal amount of chars, what the first table should contain.
        
        Returns
        -------
        best_fit : `None` or `tuple` (``TableConverter``, ``TableConverter``)
            The best fitting 2 table shard, if there is any optimal case. If there is non, returns `None` instead.
        """
        best_fit = None
        for number_of_rows in range(1, len(self.lines)-2):
            tables = self._do_break(number_of_rows)
            table_1, table_2 = tables
            if table_1.character_count > number_of_chars:
                break
            
            if not table_1._test_break():
                continue
            
            if not table_2._test_break():
                continue
            
            best_fit = tables
            continue
        
        return best_fit
    
    def render_to(self, to_extend):
        """
        Renders the table's lines to the given `list`.
        
        Parameters
        ----------
        to_extend : `list` of `str`
            A list to what the table should yield it's lines.
        """
        separator_line = self.separator_line
        to_extend.append(separator_line)
        lines = self.lines
        to_extend.extend(lines[0].lines)
        if len(lines) == 1:
            to_extend.append(separator_line)
            return
        
        to_extend.append(self.head_under_line)
        for line in lines[1:]:
            to_extend.extend(line.lines)
            to_extend.append(separator_line)
    
    def __repr__(self):
        """Returns the table's representation."""
        to_extend = [self.__class__.__name__, ':\n']
        self.render_to(to_extend)
        to_extend.append('<<END>>')
        return ''.join(to_extend)

class CodeBlockConverter(object):
    """
    Converter class for code blocks, when building text.
    
    Attributes
    ----------
    lines : `list` of `str`
        The lines of the code block.
    parentheses : `str`
        The starter and the ender line.
    """
    __slots__ = ('lines', 'parentheses', )
    def __new__(cls, code_block, indent_level, optimal_fit, builder_context):
        """
        Creates a new code block to text converter.
        
        Parameters
        ----------
        code_block : ``GravedCodeBlock``
            The source code block.
        indent_level : `int`
            The number of how far is the code block indented.
        optimal_fit : `int`
            The preferred maximal line length of the code block.
        builder_context : ``BuilderContext``
            Context to define some building details.
        
        Yields
        ------
        self : ``CodeBlockConverter``
        """
        indent = builder_context.indent*indent_level
        self = object.__new__(cls)
        self.lines = [f'{indent}{line}\n' for line in code_block.lines]
        self.parentheses = indent+'```'
        yield self
    
    @property
    def character_count(self):
        """
        Returns the code block's characters' total length.
        
        Returns
        -------
        length : `int`
        """
        lines = self.lines
        length = len(self.parentheses) <<1
        for line in lines:
            length +=len(line)
        
        return length
    
    @property
    def interactive_row_count(self):
        """
        Returns the code block reprentative interactive shell row count.
        
        Returns
        -------
        length : `int`
        """
        length = 0
        for line in self.lines:
            if line.startswith('>>>'):
                length +=1
        
        return length
    
    @property
    def code_row_count(self):
        """
        Returns how much line break is in the text.
        
        Returns
        -------
        length : `int`
        """
        last_line_void = False
        length = 0
        for line in self.lines:
            if line:
                last_line_void = False
                continue
            
            if last_line_void:
                continue
            
            last_line_void = True
            length +=1
        
        return length
    
    @property
    def line_count(self):
        """
        Returns the code block's total line count.
        
        Returns
        -------
        length : `int`
        """
        return 2+len(self.lines)
    
    @classmethod
    def _create_remove_empty_lines(cls, lines, parentheses):
        """
        Creates a new code block from the given lines and indent level.
        
        Removes the empty lines from the start and end.
        
        Parameters
        ----------
        lines : `list` of `str`
            The code block's lines.
        parentheses : `str`
            The starter and the ender line.

        Returns
        -------
        self : ``CodeBlockConverter``
        """
        while True:
            if not lines:
                break
            
            if lines[-1]:
                while True:
                    if not lines:
                        break
                    
                    if lines[0]:
                        break
                    
                    del lines[0]
                    continue
                break
            
            del lines[-1]
            continue
        
        self = object.__new__(cls)
        self.lines = lines
        self.parentheses = parentheses
        return self
    
    def _do_interactive_break(self, number_of_rows):
        """
        Does a break at the given interactive row input-output.
        
        Parameters
        ----------
        number_of_rows : `int`
            The last interactive row, what should be included in the first code block.
        
        Returns
        -------
        code_block_1 : ``CodeBlockConverter``
        code_block_2 : ``CodeBlockConverter``
        """
        rows_found = -1
        lines = self.lines
        
        index = 0
        limit = len(lines)
        while True:
            if index == limit:
                code_block_1 = self
                self._create_remove_empty_lines([], self.parentheses)
                break
            
            line = lines[index]
            if not line.startswith('>>>'):
                index +=1
                continue
            
            rows_found +=1
            if rows_found != number_of_rows:
                index +=1
                continue
            
            code_block_1 = self._create_remove_empty_lines(lines[:index], self.parentheses)
            code_block_2 = self._create_remove_empty_lines(lines[index:], self.parentheses)
            break
        
        return code_block_1, code_block_2
    
    def _test_break(self):
        """
        Returns whether this code block should be rendered alone as a broken part of a bigger one.
        
        Returns
        -------
        passed : `bool`
        """
        # At least 4 lines.
        if len(self.lines < 3):
            return False
        
        return True
        
    def _do_code_break(self, number_of_rows):
        """
        Does a break at the given interactive row input-output.
        
        Parameters
        ----------
        number_of_rows : `int`
            The last interactive row, what should be included in the first code block.
        
        Returns
        -------
        code_block_1 : ``CodeBlockConverter``
        code_block_2 : ``CodeBlockConverter``
        """
        rows_found = -1
        lines = self.lines
        last_line_void = False
        
        index = 0
        limit = len(lines)
        while True:
            if index == limit:
                code_block_1 = self
                self._create_remove_empty_lines([], self.parentheses)
                break
            
            line = lines[index]
            if line:
                last_line_void = False
                index +=1
                continue
            
            if last_line_void:
                index +=1
                continue
            
            rows_found +=1
            if rows_found != number_of_rows:
                index +=1
                continue
            
            code_block_1 = self._create_remove_empty_lines(lines[:index], self.parentheses)
            code_block_2 = self._create_remove_empty_lines(lines[index:], self.parentheses)
            break
        
        return code_block_1, code_block_2
    
    def _do_line_break(self, number_of_rows):
        """
        Does a break at the given line.
        
        Parameters
        ----------
        number_of_rows : `int`
            The first line's index, what should be not included at the first code block.
        
        Returns
        -------
        code_block_1 : ``CodeBlockConverter``
        code_block_2 : ``CodeBlockConverter``
        """
        code_block_1 = self._create_remove_empty_lines(self.lines[:number_of_rows], self.parentheses)
        code_block_2 = self._create_remove_empty_lines(self.lines[number_of_rows:], self.parentheses)
        return code_block_1, code_block_2
    
    def do_break(self, number_of_chars):
        """
        Breaks the code block to parts an returns the most optimal case for the given max chars.
        
        Parameters
        ----------
        number_of_chars : `int`
            The maximal amount of chars, what the first code block should contain.
        
        Returns
        -------
        best_fit : `None` or `tuple` (``CodeBlockConverter``, ``CodeBlockConverter``)
            The best fitting 2 code block shard, if there is any optimal case. If there is non, returns `None` instead.
        """
        
        if len(self.lines) < 6:
            return None
        
        length = self.interactive_row_count
        if length > 2:
            best_fit = None
            
            for x in range(1, length-1):
                code_blocks = self._do_interactive_break(x)
                code_block_1, code_block_2 = code_blocks
                
                if code_block_1.character_count > number_of_chars:
                    break
                
                if not code_block_1._test_break():
                    continue
                
                if not code_block_2._test_break():
                    continue
                
                best_fit = code_blocks
                continue
            
            if (best_fit is not None):
                return best_fit
        
        else:
            length = self.code_row_count
            if length > 2:
                best_fit = None
                
                for x in range(1, length-1):
                    code_blocks = self._do_code_break(x)
                    code_block_1, code_block_2 = code_blocks
                    
                    if code_block_1.character_count > number_of_chars:
                        break
                    
                    if not code_block_1._test_break():
                        continue
                    
                    if not code_block_2._test_break():
                        continue
                    
                    best_fit = code_blocks
                    continue
            
                if (best_fit is not None):
                    return best_fit
        
        if number_of_chars < 600:
            return None
        
        best_fit = None
        
        for x in range(3, len(self.lines)-3):
            code_blocks = self._do_line_break(x)
            
            if code_blocks[0].character_count > number_of_chars:
                break
            
            best_fit = code_blocks
            continue
            
        return best_fit
    
    def render_to(self, to_extend):
        """
        Renders the code block's lines to the given `list`.
        
        Parameters
        ----------
        to_extend : `list` of `str`
            A list to what the code block should yield it's lines.
        """
        parentheses = self.parentheses
        to_extend.append(parentheses)
        to_extend.extend(self.lines)
        to_extend.append(parentheses)
    
    def __repr__(self):
        """Returns the code block's representation."""
        to_extend = [self.__class__.__name__, ':\n']
        self.render_to(to_extend)
        to_extend.append('<<END>>')
        return ''.join(to_extend)


class DescriptionConverter(object):
    """
    Converter class for descriptions when building a text.
    
    Attributes
    ----------
    lines : `list` of `str`
        The lines of the description.
    indent : `int`
        The indent level of the description.
    """
    __slots__ = ('indent', 'lines', )
    def __new__(cls, description, indent_level, optimal_fit, builder_context):
        """
        Creates a new description to text converter.
        
        Parameters
        ----------
        description : ``GravedDescription``
            The source description.
        indent_level : `int`
            The number of how far is the description indented.
        optimal_fit : `int`
            The preferred maximal line length of the description.
        builder_context : ``BuilderContext``
            Context to define some building details.
        
        Yields
        ------
        self : ``DescriptionConverter``
        """
        words = builder_context.word_converter(description.content)
        lines  = sizify(words, optimal_fit)
        
        indention = builder_context.indent*indent_level
        lines = [f'{indention}{line}\n' for line in lines]
        
        self = object.__new__(cls)
        self.lines = lines
        self.indent = indent_level
        yield self
    
    @property
    def character_count(self):
        """
        Returns the description's characters' total length.
        
        Returns
        -------
        length : `int`
        """
        length = 0
        for line in self.lines:
            length +=len(line)
        
        return length
    
    @property
    def line_count(self):
        """
        Returns the description's total line count.
        
        Returns
        -------
        length : `int`
        """
        return len(self.lines)
    
    def _do_break(self, number_of_rows):
        """
        Breaks the description after the given amount of rows.
        
        Parameters
        ----------
        number_of_rows : `int`
            The number of rows before the description should be broken.
        
        Returns
        -------
        description_1 : ``DescriptionConverter``
        description_2 : ``DescriptionConverter``
        """
        description_1 = object.__new__(type(self))
        description_1.lines = self.lines[:number_of_rows]
        description_2 = object.__new__(type(self))
        description_2.lines = self.lines[number_of_rows:]
    
    def _test_break(self):
        """
        Returns whether this description should be rendered alone as a broken part of a bigger one.
        
        Returns
        -------
        passed : `bool`
        """
        if len(self.lines) < 4:
            return False
        
        if len(self.character_count) < 300:
            return False
        
        return True
    
    def do_break(self, number_of_chars):
        """
        Breaks the description to pats and returns the most optimal case for the given max chars.
        
        Parameters
        ----------
        number_of_chars : `int`
            The maximal amount of chars, what the first description should contain.

        Returns
        -------
        best_fit : `None` or `tuple` (``DescriptionConverter``, ``DescriptionConverter``)
            The best fitting 2 description shard, if there is any optimal case. If there is non, returns `None` instead.
        """
        lines = self.lines
        best_fit = None
        for x in range(4, len(lines)-4):
            descriptions = self._do_break(x)
            description_1, description_2 = descriptions
            
            if description_1.character_count > number_of_chars:
                break
            
            if not description_1._test_break():
                continue
            
            if not description_2._test_break():
                continue
            
            best_fit = descriptions
            continue
        
        return best_fit
    
    def render_to(self, to_extend):
        """
        Renders the description's lines to the given `list`.
        
        Parameters
        ----------
        to_extend : `list` of `str`
            A list to what the description should yield it's lines.
        """
        to_extend.extend(self.lines)
    
    def __repr__(self):
        """Returns the description's representation."""
        to_extend = [self.__class__.__name__, ':\n']
        self.render_to(to_extend)
        to_extend.append('<<END>>')
        return ''.join(to_extend)


def listing_converter(listing, indent_level, optimal_fit, builder_context):
    """
    Deserializes the given listing to converters.
    
    Parameters
    ----------
    listing : ``GravedListing``
        The source listing.
    indent_level : `int`
        The number of how far is the listing indented.
    optimal_fit : `int`
        The preferred maximal line length of the listing.
    builder_context : ``BuilderContext``
        Context to define some building details.
    
    Yields
    -----------
    element : `Any`
    """
    for listing_element in listing.elements:
        yield from ListingHeadConverter(listing_element.head, indent_level, optimal_fit, builder_context)
        content = listing_element.content
        if content is None:
            return
        
        yield from sub_section_converter(content, indent_level+1, optimal_fit-builder_context.indent_size, builder_context)


class ListingHeadConverter(DescriptionConverter):
    """
    Converter class for listing element heads when building a text.
    
    Attributes
    ----------
    lines : `list` of `str`
        The lines of the listing element's head.
    """
    def __new__(cls, head, indent_level, optimal_fit, builder_context):
        """
        Creates a new listing head to text converter.
        
        Parameters
        ----------
        head : `None` or `list` of (`str`, ``Grave``)
            The head of a listing.
        indent_level : `int`
            The number of how far is the listing element indented.
        optimal_fit : `int`
            The preferred maximal line length.
        builder_context : ``BuilderContext``
            Context to define some building details.
        
        Yields
        ------
        self : ``DescriptionConverter``
        """
        new_lines = []
        if head is None:
            lines = [DEFAULT_LISTING_HEAD]
        else:
            words = builder_context.word_converter(head)
            lines  = sizify(words, optimal_fit-builder_context.indent_size)
        
        new_lines.append(f'{(builder_context.indent*indent_level)}{lines[0]}\n')
        
        if len(lines)>1:
            indention = builder_context.indent*(indent_level+1)
            for line in lines[1:]:
                new_lines.append(f'{indention}{line}\n')
        
        self = object.__new__(cls)
        self.lines = new_lines
        self.indent = indent_level
        yield self


def sub_section_converter(sub_section, indent_level, optimal_fit, builder_context):
    """
    Deserializes the given sub-section to converters.
    
    Parameters
    ----------
    sub_section : `list` of `Any`
        The source sub-section..
    indent_level : `int`
        The number of how far is the sub-section indented.
    optimal_fit : `int`
        The preferred maximal line length of the sub-section.
    builder_context : ``BuilderContext``
        Context to define some building details.
    
    Yields
    -----------
    element : `Any`
    """
    for element in sub_section:
        # If the converter is a sub section converter, indent it
        converter = CONVERTER_TABLE[type(element)]
        if converter is sub_section_converter:
            local_indent_level = indent_level+1
            local_optimal_fit = optimal_fit-builder_context.indent_size
        else:
            local_indent_level = indent_level
            local_optimal_fit = optimal_fit
        
        yield from converter(element, local_indent_level, local_optimal_fit, builder_context)


CONVERTER_TABLE = {
    list : sub_section_converter,
    GravedListing : listing_converter,
    GravedDescription : DescriptionConverter,
    GravedTable : TableConverter,
    GravedCodeBlock : CodeBlockConverter,
        }


class SectionTitleConverter(DescriptionConverter):
    """
    Converter class for section titles when building a text.
    
    Attributes
    ----------
    lines : `list` of `str`
        The lines of the section title.
    """
    def __new__(cls, title):
        """
        Creates a new section title to text converter.
        
        Parameters
        ----------
        title : `None` or `str`
            The respective section's title.
        
        Yields
        ------
        self : `None` or ``DescriptionConverter``
        """
        if title is None:
            return
        
        self = object.__new__(cls)
        self.lines = [title+'\n', '-'*len(title)+'\n']
        self.indent = -2
        yield self

def should_insert_linebreak(part_1, part_2):
    """
    Returns whether there should be a linebreak inserted between the two given section parts.
    
    Parameters
    ----------
    part_1 : `Any`
        The last converter.
    part_2 : `Any`
        The next converter.
    
    Returns
    -------
    should_insert : `bool`
    """
    if not isinstance(part_1, DescriptionConverter):
        return True
    
    if isinstance(part_1, SectionTitleConverter):
        return False
    
    if not isinstance(part_2, DescriptionConverter):
        return False
    
    if part_1.indent+1 == part_2.indent:
        return False
    
    return True

def should_accept_section_break(section_1, section_2):
    """
    Returns whether the two section is correctly breaked into two parts.
    
    Note that, `section_1._test_break()` and `section_2._test_break()` should be already handled before this function is
    called.
    
    Parameters
    ----------
    section_1 : ``SectionConverter``
        The first converter.
    section_2 : ``SectionConverter``
        The second converter.
    
    Returns
    -------
    should_accept : `bool`
    """
    section_1_last = section_1.parts[-1]
    section_2_first = section_2.parts[0]
    
    if not isinstance(section_1_last, DescriptionConverter):
        return True
    
    if section_1_last.line_count > 3:
        return True
    
    if not isinstance(section_2_first, DescriptionConverter):
        return True
    
    if section_1_last.indent+1 == section_2_first.indent:
        return False
    
    return True

class SectionConverter(object):
    """
    Converter class for converting a section.
    
    Attributes
    ----------
    parts : `list` of `Any`
        The parts of the section to render.
    """
    __slots__ = ('parts', )
    def __new__(cls, section, builder_context):
        """
        Creates a new section converter.
        
        Parameters
        ----------
        section : `tuple` ((`str` or `None`), `list` of `Any`)
            The section to represent.
        builder_context : ``BuilderContext``
            Context to define some building details.
        
        Returns
        -------
        self : ``SectionConverter``
        """
        section_name, section_parts = section
        parts = [
            *SectionTitleConverter(section_name),
            *sub_section_converter(section_parts, 0, builder_context.max_line_length, builder_context)
                ]
        
        self = object.__new__(cls)
        self.parts = parts
        return self
    
    @property
    def character_count(self):
        """
        Returns the section's characters' total length.
        
        Returns
        -------
        length : `int`
        """
        length = 0
        last_part = None
        for part in self.parts:
            if should_insert_linebreak(last_part, part):
                length+=1
            
            length += part.character_count
            last_part = part
        
        return length
    
    @property
    def line_count(self):
        """
        Returns the total line count of the section.
        
        Returns
        -------
        length : `int`
        """
        length = 0
        last_part = None
        for part in self.parts:
            if should_insert_linebreak(last_part, part):
                length+=1
            
            length += part.line_count
            last_part = part
        
        return length
    
    def _do_break(self, number_of_parts):
        """
        Breaks the section at the given part index.
        
        Parameters
        ----------
        number_of_parts : `int`
            The number of parts, what the first section should contain.
        
        Returns
        -------
        section_1 : ``SectionConverter``
        section_2 : ``SectionConverter``
        """
        parts = self.parts
        section_1 = object.__new__(type(self))
        section_1.parts = parts[:number_of_parts]
        section_2 = object.__new__(type(self))
        section_2.parts = parts[number_of_parts:]
        return section_1, section_2
    
    def _do_break_middle_chared(self, middle_part_index, middle_char_limit):
        """
        Breaks the section at the given part index, and tries to break the middle element based on the given middle
        char limit as well.
        
        Parameters
        ----------
        middle_part_index : `int`
            The number of parts, what the first section should contain besides the middle element.
        middle_char_limit : `int`
            The number of chars, where the middle part should be broken.
        
        Returns
        -------
        sections : `None` or `tuple` (``SectionConverter``, ``SectionConverter``)
            Returns `None`, if the middle part cannot be broken correctly.
        """
        parts = self.parts
        if len(parts) <= middle_part_index:
            return None
        
        middle_part = parts[middle_part_index]
        middle_broken = middle_part.do_break(middle_char_limit)
        if middle_broken is None:
            return None
        
        section_1 = object.__new__(type(self))
        section_1.parts = [*parts[:middle_part_index], middle_broken[0]]
        if not section_1._test_break():
            return None
        
        section_2 = object.__new__(type(self))
        section_2.parts = [middle_broken[1], *parts[middle_part_index+1:]]
        if not section_2._test_break():
            return None
        
        if not should_accept_section_break(section_1, section_2):
            return None
        
        return section_1, section_2
    
    def _test_break(self):
        """
        Returns whether this section shard should be rendered alone.
        
        Returns
        -------
        passed : `bool`
        """
        parts = self.parts
        if len(parts) == 0:
            return False
        
        if isinstance(parts[0], SectionTitleConverter):
            min_line_count = 8
        else:
            min_line_count = 6
        
        if self.line_count < min_line_count:
            return False
        
        return True
    
    def do_break(self, number_of_chars):
        """
        Breaks the section to parts an returns the most optimal case for the given max chars.
        
        Parameters
        ----------
        number_of_chars : `int`
            The maximal amount of chars, what the first section should contain.
        
        Returns
        -------
        best_fit : `None` or `tuple` (``SectionConverter``, ``SectionConverter``)
            The best fitting 2 section shard, if there is any optimal case. If there is non, returns `None` instead.
        """
        best_fit = None
        for break_point in range(1, len(self.parts)-1):
            sections = self._do_break(break_point)
            leftover_chars = number_of_chars - sections[0].character_count
            if leftover_chars < 0:
                break
            
            sections_middled = self._do_break_middle_chared(break_point, leftover_chars)
            if (sections_middled is not None):
                best_fit = sections_middled
                continue
            
            section_1, section_2 = sections
            if not section_1._test_break():
                continue
            
            if not section_2._test_break():
                continue
            
            if not should_accept_section_break(section_1, section_2):
                continue
            
            best_fit = sections
            continue
        
        return best_fit
    
    def render_to(self, to_extend):
        """
        Renders the section to the given `list`.
        
        Parameters
        ----------
        to_extend : `list` of `str`
            A list to what the section should yield it's lines.
        """
        last_part = None
        for part in self.parts:
            if should_insert_linebreak(last_part, part):
                to_extend.append('\n')
            
            part.render_to(to_extend)
            last_part = part
    
    def __repr__(self):
        """Returns the description's representation."""
        to_extend = [self.__class__.__name__, ':\n']
        self.render_to(to_extend)
        to_extend.append('<<END>>')
        return ''.join(to_extend)

def serialize_docs_embed_sized(docs):
    """
    Serializes the docs and returns a `list` of `str`, where each element has maximal length of the size of an embed
    description.
    
    Returns
    -------
    result_chunks : `list` of `str`
    """
    result_chunks = []
    actual_chunk = []
    actual_chunk_size = 0
    
    for section in docs.sections:
        section = SectionConverter(section, EMBED_SIZED_BUILDER_CONTEXT)
        section_character_count = section.character_count
        
        limit = EMBED_DESCRIPTION_MAX_SIZE
        if actual_chunk:
            limit -=1
        
        if actual_chunk_size+section_character_count <= limit:
            if actual_chunk:
                actual_chunk.append('\n')
                actual_chunk_size +=1
            
            section.render_to(actual_chunk)
            actual_chunk_size += section_character_count
            continue
        
        leftover = limit-actual_chunk_size-1
        sections = section.do_break(leftover)
        if sections is None:
            result_chunks.append(''.join(actual_chunk))
            actual_chunk.clear()
        else:
            section_1, section = sections
            if actual_chunk:
                actual_chunk.append('\n')
            
            section_1.render_to(actual_chunk)
            result_chunks.append(''.join(actual_chunk))
            actual_chunk.clear()
            section_character_count = section.character_count
        
        while section_character_count > EMBED_DESCRIPTION_MAX_SIZE:
            sections = section.do_break(EMBED_DESCRIPTION_MAX_SIZE)
            assert sections is not None, f'Cannot break down section: {section!r}'
            
            section_1, section = sections
            section_1.render_to(actual_chunk)
            result_chunks.append(''.join(actual_chunk))
            actual_chunk.clear()
            
            section_character_count = section.character_count
            continue
        
        section.render_to(actual_chunk)
        actual_chunk_size = section_character_count
        continue
    
    if actual_chunk:
        result_chunks.append(''.join(actual_chunk))
    
    return result_chunks

def serialize_docs(docs):
    """
    Serializes the given docs to one big string.
    
    Returns
    -------
    result : `str`
    """
    result = []
    
    for section in docs.sections:
        SectionConverter(section, TEXT_BUILDER_CONTEXT).render_to(result)
    
    return ''.join(result)
    
def serialize_docs_source_text(docs):
    """
    Serializes the given docs to one big string with graves, like the source one.
    
    Returns
    -------
    result : `str`
    """
    result = []
    
    for section in docs.sections:
        SectionConverter(section, TEXT_SOURCE_BUILDER_CONTEXT).render_to(result)
    
    return ''.join(result)