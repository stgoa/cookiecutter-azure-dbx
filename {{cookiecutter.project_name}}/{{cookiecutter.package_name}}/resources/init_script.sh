#!/bin/bash
if [ -n "$EXTRA_INDEX_URL" ]; then
  PIP=$(which pip)
  for varname in ${!PRIVATE_PACKAGE_*}
    do
        echo "installing ${!varname}"
        $PIP install --extra-index-url ${EXTRA_INDEX_URL} ${!varname}
  done
fi
