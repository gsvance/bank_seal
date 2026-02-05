use std::fmt::{self, Debug};

#[derive(Debug, Clone, Copy)]
pub enum Alignment {
    Left,
    Right,
    Center,
}

impl Alignment {
    fn apply(&self, string: &mut String, width: usize) {
        *string = match self {
            Self::Left => format!("{:<width$}", string),
            Self::Right => format!("{:>width$}", string),
            Self::Center => format!("{:^width$}", string),
        }
    }
}

#[derive()]
pub struct ColumnSpec<R: ?Sized> {
    title: &'static str,
    alignment: Alignment,
    getter: Box<dyn Fn(&R) -> String>,
}

impl<R> Debug for ColumnSpec<R> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "ColumnSpec {{ title: {:?}, alignment: {:?}, getter: ... }}",
            self.title,
            self.alignment
        )
    }
}

impl<R> ColumnSpec<R> {
    pub fn new(
        title: &'static str,
        alignment: Alignment,
        getter: impl Fn(&R) -> String + 'static
    ) -> Self {
        let getter = Box::new(getter);
        Self { title, alignment, getter }
    }

    fn get(&self, row_data: &R) -> String {
        (self.getter)(row_data)
    }
}

pub trait TableRow {
    const NUM_COLUMNS: usize;

    fn column_specs_unchecked() -> Vec<ColumnSpec<Self>>;

    fn column_specs() -> Vec<ColumnSpec<Self>> {
        let column_specs = Self::column_specs_unchecked();
        assert_eq!(column_specs.len(), Self::NUM_COLUMNS);
        column_specs
    }
}

fn compute_width(column: &Vec<String>, title: &str) -> usize {
    let data_width = column
        .iter()
        .map(|value| value.len())
        .max()
        .unwrap_or(0);
    let title_len = title.len();
    if data_width >= title_len { data_width } else { title_len }
}

fn repeat_char(ch: char, n: usize) -> String {
    (0..n).map(|_| ch).collect()
}

fn join_iterator<'a>(
    mut strings: impl Iterator<Item = &'a str>,
    separator: &str
) -> String {
    let mut joined = String::new();
    match strings.next() {
        Some(first_string) => joined.push_str(first_string),
        None => return joined,
    }
    while let Some(next_string) = strings.next() {
        joined.push_str(separator);
        joined.push_str(next_string);
    }
    joined
}

const COLUMN_SPACER: &'static str = "  ";
const HEADER_UNDERLINE: char = '-';

pub trait Table {
    fn num_columns(&self) -> usize;
    fn num_rows(&self) -> usize;
    fn column_titles_unchecked(&self) -> Vec<String>;
    fn column_alignments_unchecked(&self) -> Vec<Alignment>;
    fn fetch_row_unchecked(&self, row_index: usize) -> Vec<String>;

    fn column_titles(&self) -> Vec<String> {
        let column_titles = self.column_titles_unchecked();
        assert_eq!(column_titles.len(), self.num_columns());
        column_titles
    }

    fn column_alignments(&self) -> Vec<Alignment> {
        let column_alignments = self.column_alignments_unchecked();
        assert_eq!(column_alignments.len(), self.num_columns());
        column_alignments
    }

    fn fetch_row(&self, row_index: usize) -> Vec<String> {
        let fetched_row = self.fetch_row_unchecked(row_index);
        assert_eq!(fetched_row.len(), self.num_rows());
        fetched_row
    }

    fn tabulate(&self) -> String {
        let num_columns = self.num_columns();
        let num_rows = self.num_rows();
        let mut column_titles = self.column_titles();
        let column_alignments = self.column_alignments();

        let mut columns: Vec<Vec<String>> = (0..num_columns)
            .map(|_| Vec::new())
            .collect();
        for row_index in 0..num_rows {
            let mut row = self.fetch_row(row_index);
            for column_index in (0..num_columns).rev() {
                let column_value = row.pop()
                    .expect("row should always have num_columns elements");
                columns[column_index].push(column_value);
            }
        }

        for column_index in 0..num_columns {
            let column = &mut columns[column_index];
            let column_title = &mut column_titles[column_index];
            let column_alignment = column_alignments[column_index];
            let column_width = compute_width(column, column_title);
            for value in column.iter_mut() {
                column_alignment.apply(value, column_width);
            }
            column_alignment.apply(column_title, column_width);
        }

        let header = column_titles.join(COLUMN_SPACER);
        let table_width = header.len();
        let underline = repeat_char(HEADER_UNDERLINE, table_width);

        let mut lines = vec![header, underline];
        for row_index in 0..num_rows {
            let values = columns
                .iter()
                .map(|column| &column[row_index] as &str);
            let line = join_iterator(values, COLUMN_SPACER);
            lines.push(line);
        }

        lines.join("\n")
    }
}

impl<R: TableRow> Table for Vec<R> {
    fn num_columns(&self) -> usize {
        R::NUM_COLUMNS
    }

    fn num_rows(&self) -> usize {
        self.len()
    }

    fn column_titles_unchecked(&self) -> Vec<String> {
        R::column_specs()
            .iter()
            .map(|column_spec| String::from(column_spec.title))
            .collect()
    }

    fn column_alignments_unchecked(&self) -> Vec<Alignment> {
        R::column_specs()
            .iter()
            .map(|column_spec| column_spec.alignment)
            .collect()
    }

    fn fetch_row_unchecked(&self, row_index: usize) -> Vec<String> {
        let mut row = Vec::new();
        for column_spec in R::column_specs().iter() {
            row.push(column_spec.get(&self[row_index]));
        }
        row
    }
}
