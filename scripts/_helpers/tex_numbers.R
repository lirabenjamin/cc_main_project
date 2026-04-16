# scripts/_helpers/tex_numbers.R

#' Write/update LaTeX \newcommand macros in a .tex file.
#'
#' - Creates file if it doesn't exist.
#' - Updates existing macro if present.
#' - Appends macro otherwise.
#'
#' @param path Path to .tex file (e.g., "output/numbers/main_numbers.tex")
#' @param name Macro name WITHOUT leading backslash (e.g., "MainEffect")
#' @param value Value to write (numeric or character)
#' @param digits Digits for numeric formatting
#' @param force_latex If TRUE, treat value as literal LaTeX (no escaping)
#' @return Invisible TRUE
write_tex_command <- function(path, name, value, digits = 3, force_latex = FALSE) {
  stopifnot(is.character(path), length(path) == 1L)
  stopifnot(is.character(name), length(name) == 1L)
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)

  val <- value
  if (!force_latex) {
    if (is.numeric(value) && length(value) == 1L && !is.na(value)) {
      val <- formatC(value, format = "f", digits = digits)
      val <- sub("0+$", "", val)
      val <- sub("\\.$", "", val)
    } else {
      val <- as.character(value)
    }
    val <- gsub("\\\\", "\\\\textbackslash{}", val)
    val <- gsub("([%&#_])", "\\\\\\1", val, perl = TRUE)
  } else {
    val <- as.character(value)
  }

  line <- sprintf("\\newcommand{\\%s}{%s}", name, val)

  if (!file.exists(path)) {
    writeLines(c("% Auto-generated. Do not edit by hand.", line, ""), path)
    return(invisible(TRUE))
  }

  x <- readLines(path, warn = FALSE)
  pat <- sprintf("^\\\\newcommand\\{\\\\%s\\}\\{.*\\}$", name)

  if (any(grepl(pat, x))) {
    x[grepl(pat, x)] <- line
  } else {
    if (length(x) > 0 && nzchar(tail(x, 1))) x <- c(x, "")
    x <- c(x, line, "")
  }

  writeLines(x, path)
  invisible(TRUE)
}

#' Format a p-value for LaTeX inline use.
#' Returns e.g. "= .042" or "< .001"
fmt_p <- function(p, digits = 3) {
  if (p < .001) return("$< .001$")
  paste0("$= ", sub("^0", "", sprintf(paste0("%.", digits, "f"), p)), "$")
}

#' Write a full t-test result block for a given variable label prefix.
#' Writes: {Prefix}MeanSolo, {Prefix}MeanAI, {Prefix}T, {Prefix}DF, {Prefix}P, {Prefix}D
write_ttest_block <- function(path, prefix, solo_vals, ai_vals, d_digits = 2) {
  tt <- t.test(solo_vals, ai_vals)
  pooled_sd <- sqrt((sd(solo_vals)^2 + sd(ai_vals)^2) / 2)
  d_val <- (mean(solo_vals) - mean(ai_vals)) / pooled_sd

  write_tex_command(path, paste0(prefix, "MeanSolo"), mean(solo_vals), digits = 2)
  write_tex_command(path, paste0(prefix, "MeanAI"),   mean(ai_vals),   digits = 2)
  write_tex_command(path, paste0(prefix, "SDSolo"),   sd(solo_vals),   digits = 2)
  write_tex_command(path, paste0(prefix, "SDAI"),     sd(ai_vals),     digits = 2)
  write_tex_command(path, paste0(prefix, "NSolo"),    length(solo_vals), digits = 0)
  write_tex_command(path, paste0(prefix, "NAI"),      length(ai_vals),   digits = 0)
  write_tex_command(path, paste0(prefix, "T"),        abs(tt$statistic), digits = 2)
  write_tex_command(path, paste0(prefix, "DF"),       tt$parameter, digits = 0)
  write_tex_command(path, paste0(prefix, "P"),        fmt_p(tt$p.value), force_latex = TRUE)
  write_tex_command(path, paste0(prefix, "D"),        abs(d_val), digits = d_digits)
}
