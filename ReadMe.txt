SETUP:

1. Extract all files in 'TwosPullCounterV4.zip' to a folder

2. You will need a cropped reference image of either 'Engage' or 'Start!' - I recommend 'Engage' for good consistency across different fights/arenas.
(The contained reference images may work well, depending on screen resolution and specific fight)

3. Run 'TwosPullCounter.exe'

4. Load reference image from folder - saved to config.ini when application closes

5. Choose output path and name for text file - saved to config.ini when application closes

6. Select screen region to monitor (where either 'Engage' or 'Start!' appears on your screen) - also saved to config.ini

7. Press Start to begin checking for pulls!


---------------------------------------------------------------------------


FOR OBS INTEGRATION:

1. Open OBS

2. Add a new Text (GDI+) object to the scene

3. Select Local File and point it to the text file (default 'pull_count.txt')
