%module clamav

%include "typemaps.i"
%ignore cl_engine_get_str;

%{
#include <clamav.h>
%}
%typemap(in) char ** {
  /* Check if is a list */
  if (PyList_Check($input)) {
    int size = PyList_Size($input);
    int i = 0;
    $1 = (char **) malloc((size+1)*sizeof(char *));
    for (i = 0; i < size; i++) {
      PyObject *o = PyList_GetItem($input,i);
      if (PyString_Check(o))
    $1[i] = PyString_AsString(PyList_GetItem($input,i));
      else {
    PyErr_SetString(PyExc_TypeError,"list must contain strings");
    free($1);
    return NULL;
      }
    }
    $1[i] = 0;
  } else {
    PyErr_SetString(PyExc_TypeError,"not a list");
    return NULL;
  }
}

/* This cleans up the char ** array we malloc d before the function call */


%typemap(freearg) char ** {
  free((char *) $1);
}

%typemap(argout) char ** {
  int len,i;
  PyObject *temporaire = NULL;
  len = 0;
  while ($1[len]) len++;
  len++;

  temporaire = PyList_New((Py_ssize_t)len);
//  if ($result != Py_None){
  PyList_SetItem(temporaire,0,$result);
//  } else {
//      PyList_SetItem(temporaire,0,0);
//  }
    
  for (i = 0; i < len-1; i++) {
    PyList_SetItem(temporaire,i+1,PyString_FromString($1[i]));
  }
  $result = temporaire;

}


%apply unsigned int *INOUT { unsigned int *signo };
%apply unsigned long *INOUT { unsigned long *scanned };
%include "clamav.h"

