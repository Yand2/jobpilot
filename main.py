print("JobPilot 启动成功！")

with open("data/job.txt", "r", encoding="utf-8") as file:
    job_description = file.read()

print("读取到的招聘信息：")
print(job_description)