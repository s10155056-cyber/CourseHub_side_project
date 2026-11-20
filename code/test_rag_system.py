import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_system import CourseHubRAG


class CourseHubRAGDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rag = CourseHubRAG(str(Path(__file__).resolve().parent))

    def test_loads_course_and_student_data(self):
        self.assertIn("C000001", self.rag.courses_data)
        self.assertIn("S2020001", self.rag.students_data)
        self.assertTrue(self.rag.prerequisites_data)

    def test_normalizes_fields_used_by_assistant(self):
        course = self.rag.get_course_details("C000001")
        student = self.rag.get_student_profile("S2020001")

        self.assertIn("course_name", course)
        self.assertIn("instructor", course)
        self.assertIn("time_slots", course)
        self.assertIn("gpa", student)

    def test_search_returns_matching_chinese_courses_and_source_schedule(self):
        results = self.rag.search_courses("電機", top_k=3)

        self.assertTrue(results)
        self.assertTrue(all(course["department"] == "EE" for course in results))

        course = next(
            result for result in self.rag.search_courses("C000005", top_k=1)
            if result["course_id"] == "C000005"
        )
        self.assertIn("FRI 09:00-11:00", course["time_slots"])
        self.assertIn("MON 09:00-11:00", course["time_slots"])

    def test_search_returns_courses(self):
        results = self.rag.search_courses("C000001", top_k=3)

        self.assertTrue(results)
        self.assertIn("course_name", results[0])


if __name__ == "__main__":
    unittest.main()
