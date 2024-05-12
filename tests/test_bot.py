
from unittest import TestCase
from selkie.nlp.bot import Engine

class Test (TestCase):

    def test_bot (self):

        engine = Engine(['all humans are mortal',
                         'Socrates is human',
                         'who is mortal',
                         'is Socrates mortal',
                         'is Socrates human',
                         'is Zeus human',
                         'Zeus is not mortal',
                         'is Zeus human'])
        output = engine.run()
        self.assertEqual(output, ['NPC enter\n',
                                  '> all humans are mortal\n',
                                  'NPC say OK\n',
                                  '> Socrates is human\n',
                                  'NPC say OK\n',
                                  '> who is mortal\n',
                                  'NPC say Socrates\n',
                                  '> is Socrates mortal\n',
                                  'NPC say yes\n',
                                  '> is Socrates human\n',
                                  'NPC say yes\n',
                                  '> is Zeus human\n',
                                  "NPC say I don't know\n",
                                  '> Zeus is not mortal\n',
                                  'NPC say OK\n',
                                  '> is Zeus human\n',
                                  'NPC say no\n',
                                  '\nBye\n'])
