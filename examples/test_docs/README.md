# Documentos de prueba inventados

Estos archivos son ficticios y se crearon exclusivamente para probar el extractor. No contienen preguntas de pruebas comerciales ni solicitan datos personales. Cada uno tiene **ocho ítems**; las respuestas correctas solo están indicadas en los casos señalados abajo.

| Archivo | Formato e idioma | Qué permite probar | Claves explícitas |
| --- | --- | --- | --- |
| `01_en_workshop.pdf` | PDF, inglés | Dos páginas, escala compartida, selección múltiple, verdadero/falso, emparejamiento y desarrollo. | 4: B; 5: B; 6: 1-B, 2-C, 3-A; 8: D. |
| `02_it_attivita.docx` | Word, italiano | Escala y alternativas en tablas, emparejamiento de dos columnas y claves en una sección separada. | 4: C; 5: A; 6: 1-B, 2-A, 3-C; 8: A. |
| `03_es_actividades.xlsx` | Excel, español | Escala, ítems y claves en hojas separadas; tipos mezclados. | 4: B; 5: A; 6: 1-B, 2-A, 3-C; 8: C. |
| `04_bilingue_es_en.docx` | Word, español e inglés | Dos escalas compartidas en idiomas distintos, ítems intercalados y clave bilingüe. | 5: B; 6: A. |
| `05_bilingue_it_en.xlsx` | Excel, italiano e inglés | Dos idiomas en una hoja, alternativas por fila y claves en otra hoja. | 3: B; 6: A. |

## Cómo usarlos

1. Abre la aplicación y selecciona un documento; también puedes arrastrarlo a la interfaz.
2. Revisa la vista previa y pulsa **Procesar documento**.
3. Compara el número de ítems, los textos, las alternativas y las claves explícitas con el documento original.
4. Verifica que el sistema no invente respuestas para los demás ítems y revisa las advertencias de la interfaz.

Los documentos bilingües son casos de observación, **no pruebas de un comportamiento multilingüe garantizado**. El contrato actual solo admite un código `idioma` por documento (`es`, `en`, `it` o `und`), por lo que no puede representar ambos idiomas a la vez. El LLM puede elegir uno de ellos o `und`; la pista basada en reglas puede discrepar o abstenerse. Revisa si se preserva el idioma de cada enunciado y sus opciones.

Las escalas de frecuencia pueden confundirse con selección múltiple; las claves de emparejamiento son texto compuesto. Esos casos sirven para inspeccionar limitaciones, no se corrigen automáticamente en estos documentos. El PDF contiene texto seleccionable y no requiere OCR.

## Referencia de una ejecución real

En una ejecución local con Gemini, los archivos en inglés, español y los dos bilingües devolvieron ocho ítems. El DOCX italiano devolvió `502 / llm_invalid_schema`; la estructura y las tablas del documento son intencionadamente más exigentes. En esa misma ejecución, el XLSX italiano-inglés clasificó algunas escalas como selección múltiple. Estos resultados **no son salidas esperadas garantizadas**: el modelo, la cuota y sus respuestas pueden variar entre ejecuciones. Los ejemplos no sustituyen la revisión humana.

## Regenerar archivos

Con las dependencias del backend instaladas, desde la raíz del repositorio:

```bash
python examples/test_docs/generate.py
```

El script sobrescribe únicamente los cinco archivos que genera dentro de esta carpeta. No llama a Gemini ni necesita una API key.
