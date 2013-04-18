#include <string>

namespace YouCompleteMe {

typedef struct
{
  std::string str;           // Python object with file path
  double score;              // score of string
} Match;

typedef struct
{
  std::string str;           // string to be searched
  long str_len;              // length of same
  std::string query;         // query string
  long query_len;            // length of same
  double max_score_per_char;
  int is_dot_file;           // boolean: true if str is a dot-file
} MatchObject;

double CalculateMatchScore(
  MatchObject *m,            // sharable meta-data
  long str_index,            // where in the path string to start
  long query_index,          // where in the search string to start
  long last_matched_index,   // location of last matched character
  double score);             // cumulative score so far

bool CompareMatchScore(Match a_val, Match b_val);

} // namespace YouCompleteMe
