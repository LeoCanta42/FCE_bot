import cloudconvert

api_key=(str(open("./module/timetables_operations/api_token_cloudconvert.txt","r").read())).replace('\n','')
cloudconvert.configure(api_key=api_key)

# carica il file PDF
job = cloudconvert.Job.create(payload={
    "tasks": {
        "import-my-file": {
            "operation": "import/url",
            "url":"https://www.circumetnea.it/download/orario-treni-bus/?wpdmdl=15491&refresh=64170b0d076381679231757"
        },
        "convert-my-file": {
            "operation": "convert",
            "input_format": "pdf",
            "output_format": "xlsx",
            "engine": "pdftron-pdf2excel",
            "input": [
                "import-my-file"
            ],
            "non_table_content": False,
            "single_sheet": True
        },
        "export-my-file": {
            "operation": "export/url",
            "input": [
                "convert-my-file"
            ],
            "inline": False,
            "archive_multiple_files": False
        }
    },
    "tag": "jobbuilder"
})

export_task_id = job['tasks'][2]['id']
res = cloudconvert.Task.wait(id=export_task_id)  # Wait for job completion
file = res.get("result").get("files")[0]
res = cloudconvert.download(filename=file['filename'], url=file['url'])
print(res)