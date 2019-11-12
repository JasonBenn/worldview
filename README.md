`notion-to-anki` is for exporting a Notion DB to, you guessed it, an Anki deck.

Exported notes can be found in plain text files in `~/.notion-to-anki`. They're designed to be imported into decks made of notes with 3 fields, where the first field is an ID (it's filled with the Notion document ID):

![image](https://user-images.githubusercontent.com/2539761/68641927-45889680-04c1-11ea-9b60-668ec181c498.png)

You can create a note type like this with Tools -> Manage Note Types.

If the document has changed since your last import, those changes will be reflected in the resulting flashcard without affecting your review history.
