import argparse
import json
import os
import shutil

from docimage import DocImage

ap = argparse.ArgumentParser()
ap.add_argument("-j", "--json", required=True,
                help="Path to the directory that contains the books(json file)")

ap.add_argument("-i", "--tempimg", required=True,
                help="Path to template image")

ap.add_argument("-b", "--book", required=True,
                help="give a json file name to store the segmented result(ex:->filename.json)")

ap.add_argument("-t", "--thresh", required=True,
                help="threshold value")

ap.add_argument("-d", "--dir", required=True,
                help="temporary directory")

args = vars(ap.parse_args())
jsonfile = args["json"]
tempimg = args["tempimg"]
# print tempimg
segbookfilename = args['book']
threshold1 = args['thresh']
root_dir = args['dir']
# print tempimg
bookdir = root_dir
resultimg_rootdir = root_dir
fuzzysegbookdir = root_dir
imagedir = root_dir
# print bookdir+jsonfile

basejsonfilename = os.path.basename(jsonfile)
splitbasejsonfname = basejsonfilename.split(".")
resultimages_dirname = splitbasejsonfname[0]

# code for creating folders to save result searched-images dynamically
# if folder is already exist it will override the contents inside the same folder.
storeresultimg_dir = resultimg_rootdir + resultimages_dirname
if not os.path.exists(storeresultimg_dir):
  os.makedirs(storeresultimg_dir)
else:
  shutil.rmtree(storeresultimg_dir)  # removes all the subdirectories!
  os.makedirs(storeresultimg_dir)

with open(str(bookdir + jsonfile)) as f:
  d = json.load(f)
allimages = []
allimages = d['book']['images']
# print allimages

f = open(fuzzysegbookdir + segbookfilename, 'w')
"""str2="\n{\n    \"imagepath\": "+"\""+fuzzysegbookdir+"\""+","
f.write(str2)
str3="\n    \"template-imagepath\": "+"\""+tempimg+  "\""+","
f.write(str3)
str4= "\n    \"segments\":[\n"
f.write(str4)"""

template_img = DocImage()
template_img.load(tempimg)

for i in range(len(allimages)):
  str2 = "\n{\n    \"imagepath\": " + "\"" + fuzzysegbookdir + "\"" + ","
  f.write(str2)
  str3 = "\n    \"template-imagepath\": " + "\"" + tempimg + "\"" + ","
  f.write(str3)
  str4 = "\n    \"segments\":[\n"
  f.write(str4)
  # print bookdir+allimages[i];
  splitimagename = allimages[i].split(".")
  resultimage = splitimagename[0] + "-result.jpg"

  """
  ***** this code is for preprocessing of both the source and template image and then apply template-match function.*****
  *****Gives exact match.Fuzzy-search matches are less*********"""

  next_img = DocImage()
  next_img.load(imagedir + allimages[i])
  match_locs = next_img.find(template_img, float(threshold1))
  if (len(match_locs) == 0):
    continue
  next_img.add_rectangles(match_locs)
  next_img.save(storeresultimg_dir + "/" + resultimage)
