#include <Python.h>
#include "heavy.h"

#ifdef __cplusplus
extern "C"{
#endif

static PyObject *heavycoin_gethash(PyObject *self, PyObject *args)
{
    char *output;
    PyObject *value;
    int len;
#if PY_MAJOR_VERSION >= 3
    PyBytesObject *input;
#else
    PyStringObject *input;
#endif
    if (!PyArg_ParseTuple(args, "Si", &input, &len))
        return NULL;
    Py_INCREF(input);
    output = (char*)PyMem_Malloc(32);

#if PY_MAJOR_VERSION >= 3
    heavycoin_hash((char *)PyBytes_AsString((PyObject*) input), len, output);
#else
    heavycoin_hash((char *)PyString_AsString((PyObject*) input), len, output);
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

static PyObject *heavycoin_getpowhash(PyObject *self, PyObject *args)
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
    output = (char*)PyMem_Malloc(32);

#if PY_MAJOR_VERSION >= 3
    heavycoin_hashpow((char *)PyBytes_AsString((PyObject*) input), output);
#else
    heavycoin_hashpow((char *)PyString_AsString((PyObject*) input), output);
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

static PyMethodDef HeavycoinMethods[] = {
    { "getPoWHash", heavycoin_getpowhash, METH_VARARGS, "Returns the proof of work hash using heavycoin hash" },
    { "getHash", heavycoin_gethash, METH_VARARGS, "Returns the proof of work hash using heavycoin hash" },
    { NULL, NULL, 0, NULL }
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef HeavycoinModule = {
    PyModuleDef_HEAD_INIT,
    "heavycoin_hash",
    "...",
    -1,
    HeavycoinMethods
};

PyMODINIT_FUNC PyInit_heavycoin_hash(void) {
    return PyModule_Create(&HeavycoinModule);
}

#else

PyMODINIT_FUNC initheavycoin_hash(void) {
    (void) Py_InitModule("heavycoin_hash", HeavycoinMethods);
}
#endif

#ifdef __cplusplus
}
#endif

