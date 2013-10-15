#!/bin/bash
astyle \
--style=attach \
--indent=spaces=2 \
--indent-switches \
--indent-col1-comments \
--indent-preprocessor \
--max-instatement-indent=80 \
--break-blocks \
--pad-oper \
--pad-paren-in \
--pad-header \
--keep-one-line-blocks \
--convert-tabs \
--align-pointer=name \
--align-reference=name \
--suffix=none \
--lineend=linux \
--recursive \
--exclude=gmock \
--exclude=testdata \
--exclude=ycm_client_support.cpp \
--exclude=ycm_core.cpp \
--exclude=CustomAssert.h \
--exclude=CustomAssert.cpp \
"cpp/ycm/*.cpp" \
"cpp/ycm/*.h"
