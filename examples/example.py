#%%
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from joblib import Parallel, delayed

from src.config import MAX_NJOBS

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

YYMMDD = "250515"
#%%
"""
step1. fetch
"""
from src.fetcher import fetch_papers_for_date
from src.paper import Paper

fetched_papers = fetch_papers_for_date(datetime.strptime(YYMMDD, "%y%m%d").replace(tzinfo=ZoneInfo("Asia/Tokyo")))

print(len(fetched_papers))
#%%
"""
step1.5. save and load
"""
import json

with open(Path(__file__).parent/f"fetched_example_{YYMMDD}.jsonl", "w") as f:
    for paper in fetched_papers:
        json.dump(paper.to_dict(), f, ensure_ascii=False)
        f.write("\n")

fetched_papers = []
with open(Path(__file__).parent/f"fetched_example_{YYMMDD}.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        fetched_papers.append(Paper.from_dict(json.loads(line)))
#%%
"""
step2. recommend
"""
from src.llm_utils import recommend_papers

are_recommended = recommend_papers(fetched_papers)

recommended_papers = []
other_papers = []
for is_recommended, paper in zip(are_recommended, fetched_papers):
    if is_recommended:
        recommended_papers.append(paper)
        print(f"yes: {paper.title}")
    else:
        other_papers.append(paper)
        print(f"no: {paper.title}")

print(len(recommended_papers))
#%%
"""
step4. parse
"""
from src.arxiv_html_parser import extract_fig1_authors_affils

extracted_results = Parallel(n_jobs=MAX_NJOBS, backend="threading")(
    delayed(extract_fig1_authors_affils)(paper.id) for paper in recommended_papers
)

for extracted, paper in zip(extracted_results, recommended_papers):
    paper.fig1 = extracted["fig1"]
    paper.authors = extracted["authors"]
    paper.affils = extracted["affils"]

pushing_papers = recommended_papers
#%%
"""
step5. generate
"""
from src.rss_generator import generate_rss_file

generate_rss_file(pushing_papers, other_papers, Path(__file__).parent/f"rss_example_{YYMMDD}.xml")

# %%
