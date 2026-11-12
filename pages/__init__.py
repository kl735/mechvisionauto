# coding: utf-8

from pages.ai_classification_config_page import AiClassificationConfigPage
from pages.accuracy_error_analysis_page import AccuracyErrorAnalysisPage
from pages.deep_learning_model_package_manager_page import (
    DeepLearningModelPackageManagerPage,
)
from pages.main_window_page import MainWindowPage
from pages.project_editor_page import ProjectEditorPage, StepContextMenu
from pages.project_list_page import ProjectListPage
from pages.python_package_manager_page import PythonPackageManagerPage
from pages.step_library_page import StepLibraryPage
from pages.title_bar import TitleBar
from pages.welcome_page import (
    RecentUsePanel,
    SolutionLibraryPanel,
    WelcomePage,
)

__all__ = [
    "AccuracyErrorAnalysisPage",
    "AiClassificationConfigPage",
    "DeepLearningModelPackageManagerPage",
    "MainWindowPage",
    "ProjectEditorPage",
    "ProjectListPage",
    "PythonPackageManagerPage",
    "RecentUsePanel",
    "SolutionLibraryPanel",
    "StepContextMenu",
    "StepLibraryPage",
    "TitleBar",
    "WelcomePage",
]
