//----------------DATA ACCESS LAYER------------------//

package com.example.movieactors.movie;

import org.springframework.jdbc.core.BatchPreparedStatementSetter;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

@Repository
public class MovieDataAccessService implements MovieDao {

    private final JdbcTemplate jdbcTemplate;

    public MovieDataAccessService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<Movie> selectMovies() {
        String sql = """
                SELECT id,name,release_date FROM movies LIMIT 100;
                """;
        return jdbcTemplate.query(sql, new MovieRowMapper());
    }

    @Override
    public List<Movie> selectMovieActors() {
        String sql = """
                select movies.name, actors.name from movies join actors on movies.id = actors.amovie;
                    """;
        return null;
    }

    @Override
    public int insertMovie(Movie movie) {
        String sql = """
                INSERT INTO movies(name, release_date) VALUES (?,?);
                """;
        return jdbcTemplate.update(sql, movie.name(), movie.releaseDate());
    }

    @Override
    public void insertMultipleMovies(List<Movie> movie) {
        String sql = """
                INSERT INTO movies(name, release_date) VALUES (?,?);
                """;
        jdbcTemplate.batchUpdate(sql, new BatchPreparedStatementSetter() {
            @Override
            public void setValues(PreparedStatement ps, int i)
                    throws SQLException {

                Movie m = movie.get(i);
                ps.setString(1, m.name());
                ps.setDate(2, java.sql.Date.valueOf(m.releaseDate()));

            }

            @Override
            public int getBatchSize() {
                return movie.size();
            }
        });
    }

    @Override
    public int deleteMovie(int id) {
        String sql = """
                DELETE FROM movies
                WHERE id = ?;
                """;
        return jdbcTemplate.update(sql, id);

    }

    @Override
    public Optional<Movie> selectMovieById(int id) {
        String sql = """
                SELECT id,name,release_date FROM movies WHERE id = ?;
                """;
        return jdbcTemplate.query(sql, new MovieRowMapper(), id).stream().findFirst();
    }

}
