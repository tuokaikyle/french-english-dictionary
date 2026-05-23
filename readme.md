uv run step1_truncate_book/step1.py

uv run step2_look_structure/step2.py
uv run step2_look_structure/step2.py -i step3_clean_book/step31_no_redirects.html

uv run step3_clean_book/step3.py

uv run step4_construct/step4.py

uv run step5_evaluate/step5.py

uv run z/util.py lazarone step3_clean_book/clean.html

## partitions

redirects
old

suffix 名称
pronuciation optional?

复数
or
两种词性
没有解释
translation has leading ,
