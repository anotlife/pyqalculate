"""Tests for CSV import/export functionality.

Tests:
- Calculator.importCSV() — loads CSV as matrix or per-column variables
- Calculator.exportCSV() — writes MathStructure to CSV
- load() builtin function — loads CSV in expressions
- export() builtin function — exports data in expressions
"""

import os
import tempfile

import pytest

from pyqalculate.calculator import Calculator
from pyqalculate.math_structure import MathStructure


@pytest.fixture
def calc():
    """Create a Calculator with definitions loaded."""
    c = Calculator()
    c.load_definitions()
    return c


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file with numeric data."""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(
        "Name,Score,Grade\n"
        "Alice,95,A\n"
        "Bob,87,B\n"
        "Charlie,92,A\n",
        encoding="utf-8",
    )
    return str(csv_file)


@pytest.fixture
def numeric_csv(tmp_path):
    """Create a CSV file with only numeric data."""
    csv_file = tmp_path / "numbers.csv"
    csv_file.write_text(
        "1.5,2.5,3.5\n"
        "4.5,5.5,6.5\n"
        "7.5,8.5,9.5\n",
        encoding="utf-8",
    )
    return str(csv_file)


@pytest.fixture
def semicolon_csv(tmp_path):
    """Create a CSV file with semicolon delimiter."""
    csv_file = tmp_path / "semicolon.csv"
    csv_file.write_text(
        "X;Y;Z\n"
        "10;20;30\n"
        "40;50;60\n",
        encoding="utf-8",
    )
    return str(csv_file)


class TestImportCSV:
    """Test Calculator.importCSV()."""

    def test_import_as_matrix(self, calc, numeric_csv):
        """Import CSV as a single matrix variable."""
        result = calc.importCSV(numeric_csv, headers=False, to_matrix=True, name="mymatrix")
        assert result.is_matrix()
        # Should be 3x3 (no headers)
        assert len(result) == 3
        for row in result:
            assert row.is_vector()
            assert len(row) == 3

    def test_import_as_vectors(self, calc, sample_csv):
        """Import CSV as separate column vectors."""
        result = calc.importCSV(sample_csv, headers=True, to_matrix=False, name="data")
        assert result.is_matrix()
        # Should have 3 columns
        assert len(result) == 3

    def test_import_registers_matrix_variable(self, calc, numeric_csv):
        """Import with to_matrix=True registers a matrix variable."""
        calc.importCSV(numeric_csv, to_matrix=True, name="mydata")
        var = calc.get_variable("mydata")
        assert var is not None

    def test_import_registers_column_variables(self, calc, sample_csv):
        """Import with to_matrix=False registers per-column variables."""
        calc.importCSV(sample_csv, headers=True, to_matrix=False, name="scores")
        # Should have scores_Name, scores_Score, scores_Grade
        assert calc.get_variable("scores_Name") is not None
        assert calc.get_variable("scores_Score") is not None
        assert calc.get_variable("scores_Grade") is not None

    def test_import_with_custom_delimiter(self, calc, semicolon_csv):
        """Import CSV with semicolon delimiter."""
        result = calc.importCSV(semicolon_csv, delimiter=";", to_matrix=True)
        assert result.is_matrix()
        assert len(result) == 2  # 2 data rows

    def test_import_skip_first_rows(self, calc, numeric_csv):
        """Import CSV skipping first N rows."""
        result = calc.importCSV(numeric_csv, first_row=2, headers=False, to_matrix=True)
        assert result.is_matrix()
        assert len(result) == 2  # skipped first row

    def test_import_empty_file_returns_undefined(self, calc, tmp_path):
        """Import of empty file returns undefined."""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("", encoding="utf-8")
        result = calc.importCSV(str(empty_file))
        assert result.is_undefined()

    def test_import_nonexistent_file_returns_undefined(self, calc):
        """Import of non-existent file returns undefined."""
        result = calc.importCSV("/nonexistent/path/file.csv")
        assert result.is_undefined()

    def test_import_auto_name_from_filename(self, calc, numeric_csv):
        """Import without explicit name derives from filename."""
        calc.importCSV(numeric_csv, to_matrix=True)
        var = calc.get_variable("numbers")
        assert var is not None

    def test_import_numeric_values(self, calc, numeric_csv):
        """Imported numeric cells become numbers."""
        result = calc.importCSV(numeric_csv, headers=False, to_matrix=True)
        assert result.is_matrix()
        # Check first cell is 1.5
        first_row = result[0]
        first_cell = first_row[0]
        assert first_cell.is_number()
        assert abs(first_cell.float_value() - 1.5) < 1e-10

    def test_import_string_values_become_symbols(self, calc, sample_csv):
        """Imported string cells become symbolic."""
        result = calc.importCSV(sample_csv, headers=True, to_matrix=False, name="test")
        # Name column should have symbolic values
        name_var = calc.get_variable("test_Name")
        assert name_var is not None
        from pyqalculate.variable import KnownVariable
        if isinstance(name_var, KnownVariable):
            name_vec = name_var.get()
            if name_vec is not None:
                assert name_vec.is_vector()
                first_name = name_vec[0]
                assert first_name.is_symbolic()


class TestExportCSV:
    """Test Calculator.exportCSV()."""

    def test_export_matrix(self, calc, tmp_path):
        """Export a matrix to CSV."""
        # Create a 2x3 matrix
        row1 = MathStructure.vector(MathStructure(1), MathStructure(2), MathStructure(3))
        row2 = MathStructure.vector(MathStructure(4), MathStructure(5), MathStructure(6))
        matrix = MathStructure.matrix([row1, row2])

        out_file = str(tmp_path / "output.csv")
        success = calc.exportCSV(matrix, out_file)
        assert success is True

        # Read and verify
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert "1" in lines[0]
        assert "4" in lines[1]

    def test_export_vector_as_column(self, calc, tmp_path):
        """Export a vector as a single column."""
        vec = MathStructure.vector(MathStructure(10), MathStructure(20), MathStructure(30))

        out_file = str(tmp_path / "vector.csv")
        success = calc.exportCSV(vec, out_file)
        assert success is True

        with open(out_file, encoding="utf-8") as f:
            lines = f.read().strip().split("\n")
        assert len(lines) == 3

    def test_export_single_value(self, calc, tmp_path):
        """Export a single number."""
        val = MathStructure(42)

        out_file = str(tmp_path / "single.csv")
        success = calc.exportCSV(val, out_file)
        assert success is True

        with open(out_file, encoding="utf-8") as f:
            content = f.read().strip()
        assert "42" in content

    def test_export_with_custom_delimiter(self, calc, tmp_path):
        """Export with semicolon delimiter."""
        row = MathStructure.vector(MathStructure(1), MathStructure(2))
        matrix = MathStructure.matrix([row])

        out_file = str(tmp_path / "semicolon_out.csv")
        success = calc.exportCSV(matrix, out_file, delimiter=";")
        assert success is True

        with open(out_file, encoding="utf-8") as f:
            content = f.read()
        assert ";" in content

    def test_export_invalid_path_returns_false(self, calc):
        """Export to invalid path returns False."""
        val = MathStructure(1)
        success = calc.exportCSV(val, "/nonexistent/dir/file.csv")
        assert success is False


class TestBuiltinFunctions:
    """Test load() and export() builtin functions in expressions."""

    def test_load_function_returns_matrix(self, calc, numeric_csv):
        """load(filename) returns a matrix."""
        # Escape backslashes for Windows paths
        safe_path = numeric_csv.replace("\\", "/")
        result = calc.calculate(f'load("{safe_path}")')
        assert result.is_matrix()

    def test_load_function_with_delimiter(self, calc, semicolon_csv):
        """load(filename, delimiter) works with custom delimiter via direct call."""
        # Note: semicolon cannot be passed through the expression parser
        # because ';' is the argument separator. Test via direct function call.
        load_func = calc.get_function("load")
        assert load_func is not None

        from pyqalculate.math_structure import MathStructure
        safe_path = semicolon_csv.replace("\\", "/")
        filename_arg = MathStructure.from_symbol(safe_path)
        delim_arg = MathStructure.from_symbol(";")
        result = load_func.calculate([filename_arg, delim_arg])
        assert result.is_matrix()

    def test_export_function_returns_one(self, calc, tmp_path):
        """export(data, filename) returns 1 on success."""
        out_file = str(tmp_path / "expr_export.csv").replace("\\", "/")
        # Create a matrix, export it
        result = calc.calculate(
            f'export([[1, 2], [3, 4]], "{out_file}")'
        )
        assert result.is_number()
        assert abs(result.float_value() - 1.0) < 1e-10

        # Verify file was created
        assert os.path.exists(out_file)

    def test_roundtrip_import_export(self, calc, tmp_path):
        """Import then export preserves data."""
        # Create source CSV
        src = tmp_path / "source.csv"
        src.write_text("1,2,3\n4,5,6\n", encoding="utf-8")

        # Import
        matrix = calc.importCSV(str(src), headers=False, to_matrix=True)
        assert matrix.is_matrix()

        # Export
        dst = str(tmp_path / "dest.csv")
        success = calc.exportCSV(matrix, dst)
        assert success

        # Re-import and compare
        matrix2 = calc.importCSV(dst, headers=False, to_matrix=True)
        assert matrix2.is_matrix()
        assert len(matrix) == len(matrix2)

        for r1, r2 in zip(matrix, matrix2):
            for c1, c2 in zip(r1, r2):
                assert abs(c1.float_value() - c2.float_value()) < 1e-10
