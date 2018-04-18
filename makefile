# directories specification
## directory 
DIR_TEMPLATES := xml_templates
#DIR_DOC := docs_release
## directory with python files
DIR_SRC := src
DIR_RELEASE := release
DIR_MANUAL := manual

# selection of all templates for xml generation 
FILES_J := $(patsubst %.j2,%,$(wildcard $(DIR_TEMPLATES)/*.xml.j2))
# yaml file with variables for yasha
FILE_YAML := $(DIR_TEMPLATES)/variables.yaml

# compile xml from .xml.j2 files
%.xml : %.xml.j2
	yasha $< -o $@ --variables $(FILE_YAML)

# what belongs to the complete build
all: removePYC copy xml rename zip
.PHONY: all

# remove pyc files if they occur during testing
removePYC:
	rm -f $(DIR_SRC)/los/*.pyc

# copy xml to release directory and 	
xml: $(FILES_J)
	cp $(DIR_TEMPLATES)/*.xml $(DIR_RELEASE)
	rm -f $(DIR_TEMPLATES)/*.xml
	
# empty release directory, copy docs and src to release
copy:
	rm -rf $(DIR_RELEASE)/*
#	cp -R $(DIR_DOC) $(DIR_RELEASE)/$(DIR_DOC)
	cp -R $(DIR_SRC)/* $(DIR_RELEASE)
	cp $(DIR_MANUAL)/*.pdf $(DIR_RELEASE)

# specify variables especially for rename function
rename: FILES_XML = $(wildcard $(DIR_RELEASE)/*.xml)
rename: FILES_PYT = $(wildcard $(DIR_RELEASE)/*.pyt)
# rename xml and pyt files in the build
rename:
	rename 's/-/ /gi' $(FILES_XML) $(FILES_PYT)

# zip the release folder into archive
zip:
	cd release/; zip -r ../release.zip *
	
# print variable for debuging	
print-%  : ; @echo $* = $($*)