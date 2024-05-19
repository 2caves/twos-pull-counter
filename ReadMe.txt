# TwosPullCounter ReadMe

## SETUP:

1. If you have already used the pull counter and/or own a config file, place `TwosPullCounter.exe` in the same folder. It will otherwise automatically create both the necessary `pull_count.txt` file and config file in the folder it is being opened from.

2. You will need a cropped reference image of either 'Engage' or 'Start!' - I recommend 'Engage' for good consistency across different fights/arenas. (The contained reference images MAY work well, depending on your screen resolution and specific fight)

3. Run `TwosPullCounter.exe`

4. Load reference image from folder - directory is saved to `config.ini` when application closes

5. Choose output path and name for text file - saved to `config.ini` when application closes

6. Select screen region to monitor (where either 'Engage' or 'Start!' appears on your screen) - saved to `config.ini` when application closes

7. Press Start to begin checking for pulls!

   NB. This will ONLY work if you have a consistent marker indicating the beginning of each pull (i.e countdown)

---

## FOR OBS INTEGRATION:

1. Open OBS

2. Add a new Text (GDI+) object to the scene

3. Select Local File and point it to the text file (default 'pull_count.txt')
