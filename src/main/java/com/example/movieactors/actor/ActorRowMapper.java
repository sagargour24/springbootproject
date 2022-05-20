package com.example.movieactors.actor;

import java.sql.ResultSet;
import java.sql.SQLException;

import org.springframework.jdbc.core.RowMapper;

public class ActorRowMapper implements RowMapper<Actor> {

    @Override
    public Actor mapRow(ResultSet resultSet, int rowNum) throws SQLException {
        return new Actor(
                resultSet.getInt("id"),
                resultSet.getString("name"),
                resultSet.getInt("amovie")
            );
    }
    
}
