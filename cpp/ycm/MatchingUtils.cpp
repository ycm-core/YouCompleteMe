// Copyright (C) 2011, 2012, 2013  Strahinja Val Markovic  <val@markovic.io>
//                                 Stanislav Golovanov <stgolovanov@gmail.com>
//
// This file is part of YouCompleteMe.
//
// YouCompleteMe is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// YouCompleteMe is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.
#include "MatchingUtils.h"

namespace YouCompleteMe {

double CalculateMatchScore( MatchObject *m, long str_index, long query_index,
                            long last_matched_index, double score) {

  double seen_score = 0;      // remember best score seen via recursion
  int is_dot_file_match = 0;     // true if abbrev matches a dot-file
  int dot_search = 0;         // true if searching for a dot

  for (long i = query_index; i < m->query_len; i++)
  {
      char c = m->query[i];
      if (c == '.')
          dot_search = 1;
      int found = 0;
      for (long j = str_index; j < m->str_len; j++, str_index++)
      {
          char d = m->str[j];
          if (d == '.')
          {
              if (j == 0 || m->str[j - 1] == '/')
              {
                  m->is_dot_file = 1;        // this is a dot-file
                  if (dot_search)         // and we are searching for a dot
                      is_dot_file_match = 1; // so this must be a match
              }
          }
          else if (d >= 'A' && d <= 'Z' && !(c >= 'A' && c <= 'Z'))
              d += 'a' - 'A'; // add 32 to downcase
          if (c == d)
          {
              found = 1;
              dot_search = 0;

              // calculate score
              double score_for_char = m->max_score_per_char;
              long distance = j - last_matched_index;
              if (distance > 1)
              {
                  double factor = 1.0;
                  char last = m->str[j - 1];
                  char curr = m->str[j]; // case matters, so get again
                  if (last == '/')
                      factor = 0.9;
                  else if (last == '-' ||
                          last == '_' ||
                          last == ' ' ||
                          (last >= '0' && last <= '9'))
                      factor = 0.8;
                  else if (last >= 'a' && last <= 'z' &&
                          curr >= 'A' && curr <= 'Z')
                      factor = 0.8;
                  else if (last == '.')
                      factor = 0.7;
                  else
                      // if no "special" chars behind char, factor diminishes
                      // as distance from last matched char increases
                      factor = (1.0 / distance) * 0.75;
                  score_for_char *= factor;
              }

              if (++j < m->str_len)
              {
                  // bump cursor one char to the right and
                  // use recursion to try and find a better match
                  double sub_score = CalculateMatchScore(m, j, i,
                    last_matched_index, score);

                  if (sub_score > seen_score)
                      seen_score = sub_score;
              }

              score += score_for_char;
              last_matched_index = str_index++;
              break;
          }
      }
      if (!found)
          return 0.0;
  }
  return (score > seen_score) ? score : seen_score;
}

bool CompareMatchScore(Match a_val, Match b_val)
{
  return (a_val.score > b_val.score);
}

} // namespace YouCompleteMe
