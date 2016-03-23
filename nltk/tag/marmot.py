# -*- coding: utf-8 -*-
# Natural Language Toolkit: Interface to the Marmot/Lemming POS-tagger and lemmatiser
# Inspired by the HunposTagger python interface
# Copyright (C) 2001-2015 NLTK Project
# Author: Loic Dugast <loic.dugast@gmail.com>
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

"""
A module for interfacing with the Marmot/Lemming POS-tagger and lemmatiser 
"""
from time import sleep
import os
from subprocess import Popen, PIPE

from nltk.internals import find_binary, find_file
from nltk.tag.api import TaggerI
from nltk import compat
import shlex
from ast import literal_eval

_marmot_url = 'http://code.google.com/p/hunpos/'

_marmot_charset = 'UTF-8'
##"""The default encoding used by hunpos: ISO-8859-1."""

class MarmotTagger(TaggerI):
    """
    A class for pos tagging with Marmot/Lemming. 
    Example:

        >>> from nltk.tag import MarmotTagger
        >>> mt = MarmotTagger()
        >>> mt.tag('What is the airspeed of an unladen swallow ?'.split())
    
    This class communicates with the marmot/lemming java binary via pipes. When the
    tagger object is no longer needed, the close() method should be called to
    free system resources. The class supports the context manager interface; if
    used in a with statement, the close() method is invoked automatically:

        >>> with Tagger('en_wsj.model') as ht:
        ...     ht.tag('What is the airspeed of an unladen swallow ?'.split())
        ...
        [('What', 'WP'), ('is', 'VBZ'), ('the', 'DT'), ('airspeed', 'NN'), ('of', 'IN'), ('an', 'DT'), ('unladen', 'NN'), ('swallow', 'VB'), ('?', '.')]
    """

    def __init__(self, path_to_marmot_model=None, path_to_lemming_model=None, path_to_bin=None,
                 encoding=_marmot_charset, verbose=False):
        """
        Starts the marmot executable and establishes a connection with it.

        :param path_to_model: The model file.
        :param path_to_bin: The marmot binary. Ex:  java -Xmx20g -cp marmot-2016-03-02.jar:../lib/trove.jar marmot.morph.cmd.Annotator
        :param encoding: The encoding used by the model. Unicode tokens
            passed to the tag() and tag_sents() methods are converted to
            this charset when they are sent to hunpos-tag.
            The default is ISO-8859-1 (Latin-1).

            This parameter is ignored for str tokens, which are sent as-is.
            The caller must ensure that tokens are encoded in the right charset.
        """
        self._closed = True
        marmot_path = "/home/dugasl/myGit/mycistern/marmot"
        self._marmot_bin = "/usr/bin/java"
 
        self._marmot_model = "/home/dugasl/myGit/mycistern/marmot/zul.marmot"
        self._lemming_model = "/home/dugasl/myGit/mycistern/marmot/lemming.srl"
        self._encoding = encoding
        cmd = "/usr/bin/java -Xmx5g -cp /home/dugasl/myGit/mycistern/marmot/marmot.jar:/home/dugasl/myGit/mycistern/marmot/lib/trove.jar marmot.morph.cmd.Annotator -model-file /home/dugasl/myUNISAGit/termextract/experiments/postagmodels/zul.marmot -lemmatizer-file /home/dugasl/myUNISAGit/termextract/experiments/lemmamodels/zul.lemming -test-file form-index=0,- -pred-file -"
        myout = open('/home/dugasl/myoutput.out','w')
        self._marmot = Popen(shlex.split(cmd), shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        self._closed = False

    def __del__(self):
        self.close()

    def close(self):
        """Closes the pipe to the hunpos executable."""
        if not self._closed:
            self._marmot.communicate()
            self._closed = True

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def read_one_parse(self):
        s = self._marmot.stdout.readline()
        # empty line
        emptyline = self._marmot.stdout.readline()
        parse = literal_eval(s)
        parse = [(x[0].decode(self._encoding), x[1], x[2].decode(self._encoding)) for x in parse]
        return parse

    def tag(self, tokens):
        """Tags a single sentence: a list of words.
        The tokens should not contain any newline characters.
        """
        encoded_tokens = []
        for token in tokens:
            assert "\n" not in token, "Tokens should not contain newlines"
            if isinstance(token, compat.text_type):
                token = token.encode(self._encoding)
            encoded_tokens.append(token)
        for token in encoded_tokens:
            self._marmot.stdin.write(token + b"\n")
        self._marmot.stdin.write(b"\n")
        self._marmot.stdin.flush()
        # is this useful?
        sleep(0.05)

        tagged_tokens = []
        new_parse = self.read_one_parse()
        tagged_tokens.extend(new_parse)\
        # was the full string parsed? (input may be splitted by marmot/lemming before parsing)
        while (len(tagged_tokens)<len(tokens)):
            new_parse = self.read_one_parse()
            tagged_tokens.extend(new_parse)
        assert len(tagged_tokens) == len(tokens)
        
        return tagged_tokens
    
