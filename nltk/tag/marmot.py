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

import os
from subprocess import Popen, PIPE

from nltk.internals import find_binary, find_file
from nltk.tag.api import TaggerI
from nltk import compat
import shlex

_marmot_url = 'http://code.google.com/p/hunpos/'

_marmot_charset = 'UTF-8'
##"""The default encoding used by hunpos: ISO-8859-1."""

class MarmotTagger(TaggerI):
    """
    A class for pos tagging with HunPos. The input is the paths to:
     - a model trained on training data
     - (optionally) the path to the hunpos-tag binary
     - (optionally) the encoding of the training data (default: ISO-8859-1)

    Example:

        >>> from nltk.tag import MarmotTagger
        >>> mt = MarmotTagger('en_wsj.model')
        >>> mt.tag('What is the airspeed of an unladen swallow ?'.split())
        [('What', 'WP'), ('is', 'VBZ'), ('the', 'DT'), ('airspeed', 'NN'), ('of', 'IN'), ('an', 'DT'), ('unladen', 'NN'), ('swallow', 'VB'), ('?', '.')]
        >>> mt.close()

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
        cmd = "/usr/bin/java -Xmx20g -cp /home/dugasl/myGit/mycistern/marmot/marmot-2016-03-03.jar:/home/dugasl/myGit/mycistern/marmot/lib/trove.jar marmot.morph.cmd.Annotator -model-file /home/dugasl/myGit/mycistern/marmot/zul.marmot -lemmatizer-file /home/dugasl/myGit/mycistern/marmot/lemming.srl -test-file form-index=0,tag-index=1,- -pred-file -"
        
        self._marmot = Popen(shlex.split(cmd), shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        #self._marmot = Popen([self._marmot_bin], shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE) 
        #self._marmot = Popen([self._marmot_bin, "-Xmx20g", "-cp", marmot_path+"/marmot-2016-03-03.jar:"+marmot_path+"/lib/trove.jar", "-model-file", self._marmot_model, "-lemmatizer-file", self._lemming_model, "-test-file", "form-index=0,tag-index=1,-", "-pred-file", "-"], shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
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

    def tag(self, tokens):
        """Tags a single sentence: a list of words.
        The tokens should not contain any newline characters.
        """
        for token in tokens:
            print token
            assert "\n" not in token, "Tokens should not contain newlines"
            if isinstance(token, compat.text_type):
                token = token.encode(self._encoding)
            self._marmot.stdin.write(token + b"\n")
        # We write a final empty line to tell hunpos that the sentence is finished:
        self._marmot.stdin.write(b"\n")
        self._marmot.stdin.flush()

        tagged_tokens = []
        for token in tokens:
            print self._marmot.stdout.readline()
            tagged = self._marmot.stdout.readline().strip().split(b"\t")
            tag = (tagged[1] if len(tagged) > 1 else None)
            tagged_tokens.append((token, tag))
        # We have to read (and dismiss) the final empty line:
        self._marmot.stdout.readline()

        return tagged_tokens
