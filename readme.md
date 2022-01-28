# ApacheJIT: A Large Dataset for Just-In-Time Defect Prediction

This archive contains the **ApacheJIT** dataset presented in the paper "ApacheJIT: A Large Dataset for Just-In-Time Defect Prediction" as well as the replication package. The paper is submitted to **MSR 2022 Data Showcase Track**.

The datasets are available under directory <em>dataset</em>. There are 4 datasets in this directory. 

1. **apachejit_total.csv**: This file contains the entire dataset. Commits are specified by their identifier and a set of commit metrics that are explained in the paper are provided as features. Column <em>buggy</em> specifies whether or not the commit introduced any bug into the system. 
2. **apachejit_train.csv**: This file is a subset of the entire dataset. It provides a balanced set that we recommend for models that are sensitive to class imbalance. This set is obtained from the first 14 years of data (2003 to 2016).
3. **apachejit_test_large.csv**: This file is a subset of the entire dataset. The commits in this file are the commits from the last 3 years of data. This set is not balanced to represent a real-life scenario in a JIT model evaluation where the model is trained on historical data to be applied on future data without any modification.
4. **apachejit_test_small.csv**: This file is a subset of the test file explained above. Since the test file has more than 30,000 commits, we also provide a smaller test set which is still unbalanced and from the last 3 years of data.

In addition to the dataset, we also provide the scripts using which we built the dataset. These scripts are written in Python 3.8. Therefore, Python 3.8 or above is required. To set up the environment, we have provided a list of required packages in file <em>requirements.txt</em>. Additionally, one filtering step requires GumTree [1]. For Java, GumTree requires Java 11. For other languages, external tools are needed. Installation guide and more details can be found [here](https://github.com/GumTreeDiff/gumtree/wiki/Getting-Started).

The scripts are comprised of Python scripts under directory <em>src</em> and Python notebooks under directory <em>notebooks</em>. The Python scripts are mainly responsible for conducting GitHub search via GitHub search API and collecting commits through PyDriller Package [2]. The notebooks link the fixed issue reports with their corresponding fixing commits and apply some filtering steps. The bug-inducing candidates then are filtered again using <em>gumtree.py</em> script that utilizes the GumTree package. Finally, the remaining bug-inducing candidates are combined with the clean commits in the <em>dataset_construction</em> notebook to form the entire dataset.

More specifically, <em>git_token</em> handles GitHub API token that is necessary for requests to GitHub API. Script <em>collector</em> performs GitHub search. Tracing changed lines and git annotate is done in <em>gitminer</em> using PyDriller. Finally, <em>gumtree</em> applies 4 filtering steps (number of lines, number of files, language, and change significance).

References:

**1. GumTree** 

* [https://github.com/GumTreeDiff/gumtree](https://github.com/GumTreeDiff/gumtree)

* Jean-Rémy Falleri, Floréal Morandat, Xavier Blanc, Matias Martinez, and Martin Monperrus. 2014.  Fine-grained and accurate source code differencing. In ACM/IEEE International Conference on Automated Software Engineering, ASE ’14,Vasteras, Sweden - September 15 - 19, 2014. 313–324

**2. PyDriller**

* [https://pydriller.readthedocs.io/en/latest/](https://pydriller.readthedocs.io/en/latest/)

* Davide Spadini, Maurício Aniche, and Alberto Bacchelli. 2018. PyDriller: Python Framework for Mining Software Repositories. In Proceedings of the 2018 26th ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering(Lake Buena Vista, FL, USA)(ESEC/FSE2018). Association for Computing Machinery, New York, NY, USA, 908–911
