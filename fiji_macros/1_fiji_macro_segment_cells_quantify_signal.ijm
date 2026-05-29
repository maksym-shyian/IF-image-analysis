// ====================================================
// ===== BATCH MICROSCOPY ANALYSIS MACRO ==============
// ====================================================

// === SELECT PARENT DIRECTORY ===
parentDir = getDirectory("Choose parent folder containing all experiments");
expList = getFileList(parentDir);

// ====================================================
for (e = 0; e < expList.length; e++) {

    expPath = parentDir + expList[e];
    if (!File.isDirectory(expPath)) continue;

    if (!endsWith(expPath, File.separator))
        expPath = expPath + File.separator;

    inputDir = expPath;
    print("Processing: " + inputDir);

    // ------------------------------------------------
    // Find ND file
    fileList = getFileList(inputDir);
    baseName = "";

    for (i = 0; i < fileList.length; i++) {
        if (endsWith(fileList[i], ".nd")) {
            baseName = replace(fileList[i], ".nd", "");
            break;
        }
    }

    if (baseName == "") {
        print("No ND file found. Skipping...");
        continue;
    }

    // ------------------------------------------------
    open(inputDir + baseName + ".nd");

    // ------------------------------------------------
    run("Z Project...", "projection=[Max Intensity]");
    run("Stack to Images");

    // ====================================================
    // ===== AUTO-DETECT CHANNELS ==========================
    // ====================================================

    channelList = newArray();
    prefix = "MAX_" + baseName + "_thumb_w";

    for (i = 1; i <= nImages(); i++) {

        selectImage(i);
        title = getTitle();

        if (startsWith(title, prefix)) {

            channelID = replace(title, prefix, "");

            dashPos = indexOf(channelID, "-");
            if (dashPos > 4)
                channelID = substring(channelID, 0, dashPos);

            exists = false;
            for (k = 0; k < channelList.length; k++) {
                if (channelList[k] == channelID)
                    exists = true;
            }

            if (!exists)
                channelList = Array.concat(channelList, channelID);
        }
    }

    Array.sort(channelList);

    print("Detected channels:");
    for (c = 0; c < channelList.length; c++)
        print(channelList[c]);

    // ------------------------------------------------
    // Convert channels to grayscale
    for (c = 0; c < channelList.length; c++) {
        imgName = "MAX_" + baseName + "_thumb_w" + channelList[c];
        if (isOpen(imgName)) {
            selectImage(imgName);
            run("Grays");
        }
    }

    // ====================================================
    // ===== SEGMENTATION ON FIRST CHANNEL =================
    // ====================================================

    primaryChannel = channelList[0];
    primaryImage = "MAX_" + baseName + "_thumb_w" + primaryChannel;

    selectImage(primaryImage);
    run("Duplicate...", " ");
    setOption("ScaleConversions", true);
    run("8-bit");
    run("Median...", "radius=3");
    setAutoThreshold("Huang dark no-reset");
    setOption("BlackBackground", false);
    run("Convert to Mask");
    run("Fill Holes");
    run("Watershed");

    // ------------------------------------------------
    // Background ROI creation
    run("Duplicate...", " ");
    run("Invert");
    run("Create Selection");

    if (!isOpen("ROI Manager"))
        run("ROI Manager...");

    roiManager("reset");
    roiManager("Add"); // Background ROI index = 0

    // ------------------------------------------------
    // Measure background across channels
    for (c = 0; c < channelList.length; c++) {

        selectImage("MAX_" + baseName + "_thumb_w" + channelList[c]);
        roiManager("Select", 0);
        roiManager("Measure");
    }

    saveAs("Results", inputDir + baseName + "_Results_background.csv");

    // Clear results before nuclei measurement
    if (isOpen("Results")) {
        selectWindow("Results");
        run("Clear Results");
    }

    // ====================================================
    // ===== NUCLEI DETECTION =============================
    // ====================================================

    maskImage = primaryImage + "-1";
    selectImage(maskImage);

    run("Analyze Particles...",
        "size=1000-Infinity show=[Overlay Masks] display exclude clear include summarize add");

    roiCount = roiManager("count");
    nNuclei = roiCount;

    if (nNuclei <= 0) {

        print("No nuclei detected. Skipping folder.");

        while (nImages() > 0) {
            selectImage(nImages());
            close();
        }

        roiManager("reset");

        if (isOpen("Results")) {
            selectWindow("Results");
            run("Close");
        }

        continue;
    }

    print("Detected nuclei: " + nNuclei);

    // ------------------------------------------------
    // Measure nuclei sequentially (FIXED)
    for (c = 0; c < channelList.length; c++) {

        selectImage("MAX_" + baseName + "_thumb_w" + channelList[c]);

        for (r = 0; r < roiCount; r++) {   // START FROM 0 → includes first nucleus
            roiManager("Select", r);
            roiManager("Measure");
        }
    }

    saveAs("Results", inputDir + baseName + "_Results_nuclei.csv");

    // ====================================================
    // ===== SAVE JPEG EXPORTS =============================
    // ====================================================

    for (c = 0; c < channelList.length; c++) {

        imgName = "MAX_" + baseName + "_thumb_w" + channelList[c];

        if (isOpen(imgName)) {
            selectImage(imgName);
            saveAs("Jpeg", inputDir + imgName + ".jpg");
        }
    }

    // Save segmentation masks
    if (isOpen(primaryImage + "-1")) {
        selectImage(primaryImage + "-1");
        saveAs("Jpeg", inputDir + primaryImage + "-1.jpg");
    }

    if (isOpen(primaryImage + "-2")) {
        selectImage(primaryImage + "-2");
        saveAs("Jpeg", inputDir + primaryImage + "-2.jpg");
    }

    // ====================================================
    // ===== CLEANUP ======================================
    // ====================================================

    while (nImages() > 0) {
        selectImage(nImages());
        close();
    }

    roiManager("reset");

    if (isOpen("Results")) {
        selectWindow("Results");
        run("Close");
    }
}
