use chrono::{NaiveTime, Timelike};
use clap::{Arg, Command};
use encoding_rs_io::DecodeReaderBytesBuilder;
use regex::Regex;
use std::fs::File;
use std::io::{BufReader, Read, Write};
use std::path::Path;

const WHITE: &str = "#FFFFFF";

#[derive(Debug, Clone)]
struct Subtitle {
    dialogs: std::collections::HashMap<i64, String>,
}

struct SubtitleMerger {
    subtitles: Vec<Subtitle>,
    output_path: String,
}

impl SubtitleMerger {
    fn new(output_path: &str) -> Self {
        SubtitleMerger {
            subtitles: Vec::new(),
            output_path: output_path.to_string(),
        }
    }

    fn detect_format(content: &str) -> &'static str {
        if content.contains("-->") {
            "srt"
        } else if content.contains("Dialogue:") {
            "ass"
        } else {
            "unknown"
        }
    }

    fn add(&mut self, subtitle_address: &str) -> Result<(), Box<dyn std::error::Error>> {
        let mut file = File::open(subtitle_address)?;
        let mut content = String::new();
        file.read_to_string(&mut content)?;

        let mut subtitle = Subtitle {
            dialogs: std::collections::HashMap::new(),
        };

        match Self::detect_format(&content) {
            "srt" => self.parse_srt(&content, &mut subtitle)?,
            "ass" => self.parse_ass(&content, &mut subtitle)?,
            _ => return Err("Unsupported subtitle format".into()),
        }

        self.subtitles.push(subtitle);
        Ok(())
    }

    fn parse_srt(
        &self,
        content: &str,
        subtitle: &mut Subtitle,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let time_regex =
            Regex::new(r"\d{1,2}:\d{1,2}:\d{1,2},\d{1,5} --> \d{1,2}:\d{1,2}:\d{1,2},\d{1,5}")?;

        for dialog_block in content.split("\n\n") {
            if let Some(time_match) = time_regex.find(dialog_block) {
                let time_str = time_match.as_str().split(" --> ").next().unwrap();
                let time = NaiveTime::parse_from_str(time_str, "%H:%M:%S")?;
                let timestamp =
                    time.hour() as i64 * 3600 + time.minute() as i64 * 60 + time.second() as i64;

                let text = dialog_block.replace(time_str, "").trim().to_string();

                subtitle
                    .dialogs
                    .entry(timestamp)
                    .and_modify(|existing| *existing = format!("{}\n{}", existing, text))
                    .or_insert(text);
            }
        }

        Ok(())
    }

    fn parse_ass(
        &self,
        content: &str,
        subtitle: &mut Subtitle,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let dialogue_regex = Regex::new(
            r"Dialogue:\s*\d+,(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+),.*?,.*?,.*?,.*?,.*?,.*?,(.*)",
        )?;

        for line in content.lines() {
            if let Some(caps) = dialogue_regex.captures(line) {
                let start_time_str = caps.get(1).map_or("", |m| m.as_str());
                let time = NaiveTime::parse_from_str(start_time_str, "%H:%M:%S.%3f")?;
                let timestamp =
                    time.hour() as i64 * 3600 + time.minute() as i64 * 60 + time.second() as i64;

                let text = caps.get(3).map_or("", |m| m.as_str()).to_string();

                subtitle
                    .dialogs
                    .entry(timestamp)
                    .and_modify(|existing| *existing = format!("{}\n{}", existing, text))
                    .or_insert(text);
            }
        }

        Ok(())
    }

    fn merge(&self) -> Result<(), Box<dyn std::error::Error>> {
        let mut timestamps: Vec<i64> = self
            .subtitles
            .iter()
            .flat_map(|sub| sub.dialogs.keys().cloned())
            .collect();
        timestamps.sort_unstable();
        timestamps.dedup();

        let mut output_lines = Vec::new();
        let mut count = 1;

        for timestamp in timestamps {
            for subtitle in &self.subtitles {
                if let Some(dialog) = subtitle.dialogs.get(&timestamp) {
                    let line = format!("{}\n{}\n", count, dialog);
                    output_lines.push(line);
                    count += 1;
                }
            }
        }

        let mut output_file = File::create(&self.output_path)?;
        output_file.write_all(output_lines.join("\n").as_bytes())?;

        println!("'{}' created successfully.", self.output_path);
        Ok(())
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let matches = Command::new("subtitle-merger")
        .about("Merge subtitle files")
        .arg(Arg::new("input1").index(1).required(true))
        .arg(Arg::new("input2").index(2).required(true))
        .arg(Arg::new("output").index(3).required(true))
        .get_matches();

    let input1 = matches.get_one::<String>("input1").unwrap();
    let input2 = matches.get_one::<String>("input2").unwrap();
    let output = matches.get_one::<String>("output").unwrap();

    let mut merger = SubtitleMerger::new(output);
    merger.add(input1)?;
    merger.add(input2)?;
    merger.merge()?;

    Ok(())
}
