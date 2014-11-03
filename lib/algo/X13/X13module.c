#include <Python.h>

#include "X13.h"

static PyObject *X13_getpowhash(PyObject *self, PyObject *args)
{
    char *output;
    PyObject *value;
#if PY_MAJOR_VERSION >= 3
    PyBytesObject *input;
#else
    PyStringObject *input;
#endif
    if (!PyArg_ParseTuple(args, "S", &input))
        return NULL;
    Py_INCREF(input);
    output = PyMem_Malloc(32);

#if PY_MAJOR_VERSION >= 3
    X13_hash((char *)PyBytes_AsString((PyObject*) input), output);
#else
    X13_hash((char *)PyString_AsString((PyObject*) input), output);
#endif
    Py_DECREF(input);
#if PY_MAJOR_VERSION >= 3
    value = Py_BuildValue("y#", output, 32);
#else
    value = Py_BuildValue("s#", output, 32);
#endif
    PyMem_Free(output);
    return value;
}

static PyMethodDef X13Methods[] = {
    { "getPoWHash", X13_getpowhash, METH_VARARGS, "Returns the proof of work hash using X13 hash" },
    { NULL, NULL, 0, NULL }
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef X13Module = {
    PyModuleDef_HEAD_INIT,
    "X13_hash",
    "...",
    -1,
    X13Methods
};

PyMODINIT_FUNC PyInit_X13_hash(void) {
    return PyModule_Create(&X13Module);
}

#else

PyMODINIT_FUNC initX13_hash(void) {
    (void) Py_InitModule("X13_hash", X13Methods);
}
#endif
