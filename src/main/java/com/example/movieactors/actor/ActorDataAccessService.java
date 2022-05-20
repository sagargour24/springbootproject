package com.example.movieactors.actor;

import java.util.List;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class ActorDataAccessService implements ActorsDao {

    private final JdbcTemplate jdbcTemplate;

    public ActorDataAccessService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<Actor> selectActors() {
        String sql = """
                SELECT id, name, movie FROM actors LIMIT 100;
                """;
        return jdbcTemplate.query(sql, new ActorRowMapper());
    }

    @Override
    public int insertActor(Actor actor) {
        String sql = """
                INSERT INTO actors(name, amovie) VALUES(?,?);
                """;
        return jdbcTemplate.update(sql, actor.name(), actor.amovie());
    }

}
